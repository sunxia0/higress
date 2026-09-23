import pathlib,os,json,subprocess,datetime,hashlib
root=pathlib.Path(__file__).resolve().parent; out=root/'kind';repo=pathlib.Path('/Users/xiao/.codex/worktrees/8e59/higress-fork')
env={k:v for k,v in os.environ.items() if k not in ('GH_TOKEN','GITHUB_TOKEN')}
env.update(KUBECONFIG=str(out/'kubeconfig'),KIND_EXPERIMENTAL_PROVIDER='podman')
rec={'token_overrides_unset':True,'cluster':'mcp-auto-followup-4685','commands':[]}
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(name,cmd,stdout=None):
 item={'name':name,'command':cmd,'started_at':now(),'log':name+'.log'}
 with (out/item['log']).open('w') as log:
  if stdout:
   with stdout.open('w') as target:r=subprocess.run(cmd,cwd=repo,env=env,stdout=target,stderr=log)
  else:r=subprocess.run(cmd,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
 item.update(exit_code=r.returncode,finished_at=now());rec['commands'].append(item)
 (out/'setup-recovery-results.json').write_text(json.dumps(rec,indent=2));print(json.dumps(item),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
run('install-crds',['kubectl','apply','--server-side','-f','helm/core/crds/customresourcedefinitions.gen.yaml','-f','helm/core/crds/istio-envoyfilter.yaml'])
run('install-after-crds',['kubectl','apply','-f',str(out/'manifest.yaml')])
run('base',['kubectl','apply','-f',str(out/'base-mcp-only.yaml')])
run('wait-controller',['kubectl','rollout','status','deployment/higress-controller','-n','higress-system','--timeout=180s'])
run('wait-gateway',['kubectl','rollout','status','deployment/higress-gateway','-n','higress-system','--timeout=180s'])
run('stop-before-runtime',['podman','stop','mcp-auto-followup-4685-control-plane'])
rec['pass']=True;rec['config_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'cluster.yaml',out/'values.yaml',out/'manifest.yaml',out/'base-mcp-only.yaml']}
(out/'setup-recovery-results.json').write_text(json.dumps(rec,indent=2));print('kind prepared and stopped',flush=True)
