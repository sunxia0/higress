#!/usr/bin/env python3
"""Exact-session oracle against the unmodified candidate Wasm in real Envoy."""
import concurrent.futures
import copy
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

MODERN = "2026-07-28"
EXPECTED = ["server/discover", "initialize", "notifications/initialized", "tools/call"]


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def validate(events):
    require(len(events) == 8, "expected exactly two independent four-call exchanges")
    for key in ("alice", "bob"):
        own = [event for event in events if event["requestKey"] == key]
        require([event["rpcMethod"] for event in own] == EXPECTED, "operation sequence mismatch for " + key)
        require(all(event["authAlias"] == key for event in own), "credential identity mismatch for " + key)
        require(all(event.get("unexpectedEarlySession") is False for event in own), "session leaked into a control request")
        require([event.get("requestSessionMatches") for event in own] == [None, None, True, True],
                "initialized/business session does not match current request identity: " + key)
        require(all(event["path"] == "/auto/mcp" and event["authority"] == "backend-primary:8080" for event in own),
                "target changed across phases")


def self_test():
    from session_backend import session_identity
    events = []
    for key in ("alice", "bob"):
        for method in EXPECTED:
            session = "auto-session-" + key if method in EXPECTED[2:] else ""
            events.append({"requestKey": key, "rpcMethod": method, "authAlias": key,
                           "path": "/auto/mcp", "authority": "backend-primary:8080",
                           **session_identity(method, key, session)})
    validate(events)
    negatives = []
    for method in EXPECTED[2:]:
        swapped = copy.deepcopy(events)
        for row in swapped:
            if row["rpcMethod"] == method:
                other = "bob" if row["requestKey"] == "alice" else "alice"
                row.update(session_identity(method, row["requestKey"], "auto-session-" + other))
        try:
            validate(swapped)
        except AssertionError:
            negatives.append({"phase": method, "swappedSessionRejected": True})
        else:
            raise AssertionError("oracle accepted swapped sessions in " + method)
    return {"positive": True, "negativeControls": negatives, "rawSessionValuesPublished": False}


def exchange(url, value=None, headers=None):
    request = urllib.request.Request(url, data=None if value is None else json.dumps(value).encode(),
                                     headers=headers or {}, method="GET" if value is None else "POST")
    try:
        response = urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read()
        try:
            body = json.loads(raw) if raw else None
        except ValueError:
            body = None
        return response.status, body


def wait(read, predicate, description, seconds=45):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            value = read()
            if predicate(value):
                return value
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.02)
    raise AssertionError("timeout: " + description)


def run():
    gateway = os.environ.get("MCP_SUPPLEMENT_GATEWAY", "gateway")
    root = Path(os.environ.get("RUNTIME_EVIDENCE", "."))
    evidence = {"sourceSha": os.environ["MCP_EXPECTED_SOURCE_SHA"], "status": "FAIL", "oracle": self_test()}
    backend_url = "http://backend-primary:8080"
    state = lambda: exchange(backend_url + "/__state")[1]
    release = lambda: exchange(backend_url + "/__auto_release", {"stage": "initialize"})
    try:
        wait(lambda: exchange(f"http://{gateway}:9901/ready"), lambda value: value[0] == 200, "Envoy ready")
        require(exchange(backend_url + "/__reset", {})[0] == 200, "backend reset failed")
        require(exchange(backend_url + "/__auto_config", {"case": "supplement-concurrent-legacy", "mode": "legacy-session", "barrier": "initialize"})[0] == 200,
                "backend configure failed")
        def call(key):
            return exchange(f"http://{gateway}:10011/mcp", {
                "jsonrpc": "2.0", "id": "supplement-" + key, "method": "tools/call",
                "params": {"name": "proxy_echo", "arguments": {"value": "fixture"}, "_meta": {
                    "io.modelcontextprotocol/protocolVersion": MODERN,
                    "io.modelcontextprotocol/clientInfo": {"name": "supplement", "version": "1"},
                    "io.modelcontextprotocol/clientCapabilities": {}}}}, {
                "Host": "mcp.runtime.test", "Content-Type": "application/json", "Accept": "application/json,text/event-stream",
                "MCP-Protocol-Version": MODERN, "Mcp-Method": "tools/call", "Mcp-Name": "proxy_echo",
                "baggage": key, "Authorization": "Bearer auto-" + key, "X-Request-ID": "supplement-" + key})
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            pending = {key: pool.submit(call, key) for key in ("alice", "bob")}
            try:
                at_barrier = wait(state, lambda value: {event["requestKey"] for event in value["events"] if event["rpcMethod"] == "initialize"} == {"alice", "bob"},
                                  "both identities at initialize", seconds=8)
                require(all(not future.done() for future in pending.values()), "requests did not overlap at the barrier")
                require(all(event["rpcMethod"] in EXPECTED[:2] for event in at_barrier["events"]), "business advanced before barrier release")
                evidence["bothInitializeRequestsObservedBeforeRelease"] = True
                require(release()[0] == 200, "release failed")
                evidence["responses"] = {}
                for key, future in pending.items():
                    status, body = future.result()
                    require(status == 200 and isinstance(body, dict) and "result" in body, "candidate tool call failed for " + key)
                    evidence["responses"][key] = {"status": status, "hasResult": True}
            finally:
                release()
        observed = state()
        validate(observed["events"])
        require(observed["auto"]["executions"] == {"alice": 1, "bob": 1}, "unexpected business executions")
        # Publish only pseudonyms and exact-comparison booleans, never sessions.
        fields = ("requestKey", "rpcMethod", "authAlias", "requestSessionMatches", "unexpectedEarlySession")
        evidence["events"] = [{name: event[name] for name in fields} for event in observed["events"]]
        evidence["executions"] = observed["auto"]["executions"]
        evidence["accessRequestIds"] = ["supplement-alice", "supplement-bob"]
        evidence["status"] = "PASS"
        return 0
    except Exception as error:
        evidence["error"] = str(error)
        return 1
    finally:
        (root / "session-isolation.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": evidence["status"], "evidence": str(root / "session-isolation.json")}))


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        sys.exit(run())
