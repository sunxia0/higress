#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

root = Path(os.environ["RUNTIME_EVIDENCE"])
run = json.loads((root / "session-isolation.json").read_text())
identity = json.loads((root / "identity.json").read_text())
log = (root / "gateway.log").read_text(errors="replace")
observed = re.findall(r"access request_id=([^ ]+)", log)
expected = run.get("accessRequestIds", [])
cleanup = (root / "cleanup-proof.txt").read_text().strip()
passed = (run["status"] == "PASS" and len(expected) == 2 and Counter(observed) == Counter(expected)
          and all(value == 1 for value in Counter(observed).values()) and cleanup.startswith("PASS no containers remain"))
manifest = {"status": "PASS" if passed else "FAIL", **identity,
            "accessCoverage": {"expected": expected, "observed": observed, "matches": Counter(observed) == Counter(expected)},
            "cleanup": cleanup, "runtimeBoundary": "unmodified candidate Wasm and Envoy config; backend-only exact-session instrumentation"}
(root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
checksums = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in sorted(root.iterdir())
             if path.is_file() and path.name != "SHA256SUMS"]
(root / "SHA256SUMS").write_text("\n".join(checksums) + "\n")
print(json.dumps(manifest, sort_keys=True))
sys.exit(0 if passed else 1)
