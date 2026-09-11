#!/usr/bin/env python3
"""Strict raw HTTP companion to the SDK's generic exception assertion."""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--endpoint", required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
version = "2026-07-28"
rpc_id = "supplement-probe-error"
body = {"jsonrpc": "2.0", "id": rpc_id, "method": "tools/call", "params": {
    "name": "get_weather", "arguments": {"location": "New York"}, "_meta": {
        "io.modelcontextprotocol/protocolVersion": version,
        "io.modelcontextprotocol/clientInfo": {"name": "supplement", "version": "1"},
        "io.modelcontextprotocol/clientCapabilities": {}}}}
request = urllib.request.Request(args.endpoint + "/proxy-auto-error", data=json.dumps(body).encode(), headers={
    "Content-Type": "application/json", "Accept": "application/json,text/event-stream",
    "MCP-Protocol-Version": version, "Mcp-Method": "tools/call", "Mcp-Name": "get_weather"})
evidence = {"accepted": False}
try:
    try:
        response = urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read()
        evidence["httpStatus"] = response.status
    try:
        result = json.loads(raw)
    except ValueError:
        result = None
    code = (result.get("error") or {}).get("code") if isinstance(result, dict) else None
    evidence.update({"rpcErrorCode": code, "idMatches": isinstance(result, dict) and result.get("id") == rpc_id,
                     "fixtureSequenceFailure": raw.startswith(b"callout sequence [server/discover tools/call], want [server/discover]")})
    evidence["accepted"] = evidence["httpStatus"] == 400 and code == -32020 and evidence["idMatches"] and result.get("jsonrpc") == "2.0" and "result" not in result
    status = 0 if evidence["accepted"] else 42
except Exception as error:
    evidence["checkerFailure"] = type(error).__name__
    status = 3
args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
print(json.dumps(evidence, sort_keys=True))
sys.exit(status)
