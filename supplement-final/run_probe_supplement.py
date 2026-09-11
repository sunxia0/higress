#!/usr/bin/env python3
"""Build the unchanged SDK fixture and an isolated sequence-fault overlay.

The overlay adds a synthetic extra business record to the fixture's existing
sequence oracle. It does not alter production MCP code or claim real business
execution. The fixture's real HTTP 500 path must be rejected by the raw checker.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--source", required=True, help="exact final candidate source SHA")
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
HEAD = args.source
assert len(HEAD) == 40 and all(char in "0123456789abcdef" for char in HEAD)
repo, out = args.repo.resolve(), args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
script_dir = Path(__file__).resolve().parent
extension = repo / "plugins/wasm-go/extensions/mcp-server"
source = extension / "testdata/interop/host/main.go"
original = source.read_bytes()
assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() == HEAD
assert not subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip()
needle = "\tverify := func() error {\n"
assert original.decode().count(needle) == 1
injection = needle + '\t\tif profile == "error" && os.Getenv("MCP_SUPPLEMENT_EXTRA_BUSINESS") == "1" {\n\t\t\tobserved = append(observed, "tools/call")\n\t\t}\n'
variant = out / "host-sequence-fault.go"
variant.write_text(original.decode().replace(needle, injection))
overlay = out / "overlay.json"
overlay.write_text(json.dumps({"Replace": {str(source): str(variant)}}, indent=2))
results = {"sourceSha": HEAD, "productionSourcesUnchanged": True, "originalFixtureSha256": hashlib.sha256(original).hexdigest(),
           "overlayFixtureSha256": hashlib.sha256(variant.read_bytes()).hexdigest(), "scenarios": [], "status": "FAIL"}
try:
    for scenario, fault in (("unchanged-fixture", False), ("extra-business-sequence-fault", True)):
        binary = out / (scenario + "-host")
        command = ["go", "-C", str(extension), "build", "-trimpath"]
        if fault:
            command += ["-overlay", str(overlay)]
        command += ["-o", str(binary), "./testdata/interop/host"]
        with (out / (scenario + "-build.log")).open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        ready = out / (scenario + "-endpoint")
        ready.unlink(missing_ok=True)
        environment = dict(os.environ)
        if fault:
            environment["MCP_SUPPLEMENT_EXTRA_BUSINESS"] = "1"
        with (out / (scenario + "-host.log")).open("w") as log:
            host = subprocess.Popen([str(binary), "-ready-file", str(ready)], stdout=log, stderr=subprocess.STDOUT, env=environment)
            try:
                deadline = time.monotonic() + 15
                while not ready.exists() and time.monotonic() < deadline:
                    if host.poll() is not None:
                        raise RuntimeError("fixture exited before readiness")
                    time.sleep(0.02)
                if not ready.exists():
                    raise RuntimeError("fixture readiness timeout")
                record_path = out / (scenario + ".json")
                checked = subprocess.run([sys.executable, str(script_dir / "raw_probe_oracle.py"), "--endpoint", ready.read_text(), "--out", str(record_path)],
                                         capture_output=True, text=True)
                observed = json.loads(record_path.read_text())
                if fault:
                    assert checked.returncode == 42 and observed["httpStatus"] == 500 and observed["fixtureSequenceFailure"] and not observed["accepted"], observed
                else:
                    assert checked.returncode == 0 and observed["httpStatus"] == 400 and observed["rpcErrorCode"] == -32020 and observed["accepted"], observed
                results["scenarios"].append({"scenario": scenario, "oracleExit": checked.returncode, "expected": True,
                                             "binarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(), **observed})
            finally:
                host.terminate()
                try:
                    host.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    host.kill()
                    host.wait(timeout=5)
                # Directly execute a built binary, avoiding go-run child leaks.
                results.setdefault("cleanup", []).append({"scenario": scenario, "hostExited": host.poll() is not None})
        assert source.read_bytes() == original
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() == HEAD
    assert not subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip()
    results["status"] = "PASS"
finally:
    (out / "probe-oracle-summary.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": results["status"], "evidence": str(out / "probe-oracle-summary.json")}))
