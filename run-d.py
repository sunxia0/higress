import os, sys, subprocess, pathlib, json, datetime, hashlib
repo = pathlib.Path("/Users/xiao/.codex/worktrees/8e59/higress-fork")
evidence = pathlib.Path(sys.argv[1])
evidence.mkdir(parents=True, exist_ok=False)
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
if status:
    raise SystemExit("Final verification requires a clean tracked source tree: " + status)
ext = repo / "plugins/wasm-go/extensions/mcp-server"
shared = repo / "plugins/wasm-go/pkg/mcp"
runtime = ext / "testdata/runtime-verification"
commands = [
    ("auto-self-tests", ["python3", str(runtime / "auto_self_test.py")], {}),
    ("orchestration-self-tests", ["python3", str(runtime / "orchestration_self_test.py")], {}),
    ("lifecycle-self-tests", ["bash", str(runtime / "lifecycle_self_test.sh")], {}),
    ("release-unit", ["go", "-C", str(repo / "tools/plugin-release"), "test", "-run", "TestFirstManagedRelease", "-count=1", "./..."], {}),
    ("catalog", ["go", "-C", str(repo / "tools/plugin-release"), "run", ".", "validate-catalog", "--root", "../..", "--catalog", "../../plugins/release/catalog.json"], {}),
    ("unit", ["go", "-C", str(shared), "test", "-count=1", "./..."], {}),
    ("race", ["go", "-C", str(shared), "test", "-race", "-count=1", "./server", "./protocol"], {}),
    ("extension", ["go", "-C", str(ext), "test", "-count=1", "./..."], {}),
    ("interop", ["bash", str(ext / "testdata/interop/run.sh")], {}),
    ("wasm", ["go", "-C", str(ext), "build", "-trimpath", "-buildmode=c-shared", "-o", str(evidence / "plugin.wasm"), "."], {"GOOS": "wasip1", "GOARCH": "wasm"}),
]
records = {"source_sha": head, "source_tree_clean": True, "started_at": now(), "commands": [], "toolchain": {}, "token_overrides_unset": True}
for name, cmd in [("go", ["go", "version"]), ("node", ["node", "--version"])]:
    records["toolchain"][name] = subprocess.check_output(cmd, text=True).strip()
for name, cmd, overrides in commands:
    item = {"name": name, "command": cmd, "environment_overrides": overrides, "started_at": now(), "log": name + ".log"}
    with (evidence / item["log"]).open("w") as log:
        run = subprocess.run(cmd, cwd=repo, env=dict({k:v for k,v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}, **overrides), stdout=log, stderr=subprocess.STDOUT)
    item.update(exit_code=run.returncode, finished_at=now())
    records["commands"].append(item)
    (evidence / "results.json").write_text(json.dumps(records, indent=2))
    print(json.dumps(item), flush=True)
records["finished_at"] = now()
records["unchanged_head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == head
records["final_status"] = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
for name in ["plugin.wasm"] + [item["log"] for item in records["commands"]]:
    file = evidence / name
    if file.exists():
        records.setdefault("sha256", {})[name] = hashlib.sha256(file.read_bytes()).hexdigest()
records["pass"] = all(x["exit_code"] == 0 for x in records["commands"]) and records["unchanged_head"] and not records["final_status"]
(evidence / "results.json").write_text(json.dumps(records, indent=2))
print(json.dumps(records), flush=True)
raise SystemExit(0 if records["pass"] else 1)
