import os,sys,json,subprocess,pathlib,datetime,hashlib,re,shutil
repo=pathlib.Path("/Users/xiao/.codex/worktrees/8e59/higress-fork")
root=pathlib.Path(__file__).resolve().parent
source=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=False)
d=json.loads((source/"results.json").read_text()); head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()
assert d["pass"] and d["source_sha"]==head
assert not subprocess.check_output(["git","status","--porcelain"],cwd=repo,text=True)
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
record={"source_sha":head,"started_at":now(),"commands":[],"adaptation":"../kind/environment-adaptation.json","token_overrides_unset":True}
env=dict({k:v for k,v in os.environ.items() if k not in ("GH_TOKEN","GITHUB_TOKEN")},KUBECONFIG=str(root/"kind/kubeconfig"),KIND_EXPERIMENTAL_PROVIDER="podman")
def save(): (out/"results.json").write_text(json.dumps(record,indent=2))
def run(name,cmd,extra=None,check=True):
 item={"name":name,"command":cmd,"started_at":now(),"log":name+".log"}
 with (out/item["log"]).open("w") as log:
  r=subprocess.run(cmd,cwd=repo,env=dict(env,**(extra or {})),stdout=log,stderr=subprocess.STDOUT)
 item.update(exit_code=r.returncode,finished_at=now());record["commands"].append(item);save();print(json.dumps(item),flush=True)
 if check and r.returncode: raise RuntimeError("failed "+name)
 return r.returncode
try:
 run("compile",["go","test","-c","-tags","conformance","-o",str(out/"conformance.test"),"./test/e2e/e2e_test.go"],{"CGO_ENABLED":"0","GOOS":"linux","GOARCH":"arm64"})
 wasm=source/"plugin.wasm"
 assert hashlib.sha256(wasm.read_bytes()).hexdigest()==d["sha256"]["plugin.wasm"]
 shutil.copyfile(wasm,repo/"plugins/wasm-go/extensions/mcp-server/plugin.wasm")
 run("start-node",["podman","start","mcp-auto-followup-4685-control-plane"])
 run("load-python",["kind","load","image-archive","--name","mcp-auto-followup-4685",str(root/"kind/image-3.tar")])
 run("wait-api",["python3","-c","import subprocess,time,sys\ndeadline=time.monotonic()+120\nwhile time.monotonic()<deadline:\n r=subprocess.run(['kubectl','--request-timeout=5s','get','deployment/higress-controller','-n','higress-system'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)\n if r.returncode==0: print('API and deployment authorization ready');sys.exit(0)\n time.sleep(2)\nraise SystemExit('API/deployment authorization did not become ready')"])
 run("wait-controller",["kubectl","rollout","status","deployment/higress-controller","-n","higress-system","--timeout=120s"])
 run("restart-gateway",["kubectl","rollout","restart","deployment/higress-gateway","-n","higress-system"])
 run("wait-gateway",["kubectl","rollout","status","deployment/higress-gateway","-n","higress-system","--timeout=120s"])
 run("copy-test",["podman","cp",str(out/"conformance.test"),"mcp-auto-followup-4685-control-plane:/conformance.test"])
 code=run("conformance",["podman","exec","-e","KUBECONFIG=/etc/kubernetes/admin.conf","mcp-auto-followup-4685-control-plane","/conformance.test","-test.v","-test.timeout=8m","-isWasmPluginTest=true","-wasmPluginType=GO","-wasmPluginName=mcp-server","--ingress-class=higress","--debug=true","--test-area=run","--execute-tests=WasmPluginsMCP20260728"],check=False)
 log=(out/"conformance.log").read_text()
 observed=set(re.findall(r"--- PASS: TestHigressConformanceTests/WasmPluginsMCP20260728/([^ ]+)",log))
 expected={"modern_discovery","modern_tools/list","modern_tools/call","legacy_tools/list_remains_unshaped","cross-origin_request_rejected","auto_modern_discovers_before_direct_call","auto_legacy_discovers_before_direct_call"}
 record.update(expected_cases=sorted(expected),passed_cases=sorted(observed),pass_=code==0 and observed==expected and "--- FAIL:" not in log)
 run("gateway-log",["kubectl","logs","-n","higress-system","deployment/higress-gateway"],check=False)
 run("image-identities",["podman","exec","mcp-auto-followup-4685-control-plane","ctr","-n","k8s.io","images","list"],check=False)
 record["sha256"]={"plugin.wasm":d["sha256"]["plugin.wasm"],"conformance.test":hashlib.sha256((out/"conformance.test").read_bytes()).hexdigest()}
except Exception as exc:
 record.update(pass_=False,error=str(exc))
finally:
 record["finished_at"]=now();save();print(json.dumps(record),flush=True)
raise SystemExit(0 if record.get("pass_") else 1)
