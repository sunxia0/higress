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
 (out/'setup-results.json').write_text(json.dumps(rec,indent=2));print(json.dumps(item),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
run('create',['kind','create','cluster','--name',rec['cluster'],'--image','docker.io/kindest/node:v1.32.2','--config',str(out/'cluster.yaml'),'--kubeconfig',str(out/'kubeconfig'),'--wait','120s'])
images=['higress-registry.cn-hangzhou.cr.aliyuncs.com/higress/'+x+':v2.2.3' for x in ['higress','pilot','gateway']]+['docker.io/library/python:3.12-alpine','higress-registry.cn-hangzhou.cr.aliyuncs.com/higress/echo-server:1.3.0']
for i,image in enumerate(images):
 if subprocess.run(['podman','image','exists',image],env=env).returncode:
  run('pull-'+str(i),['podman','pull',image])
 archive=out/f'image-{i}.tar'
 run('save-'+str(i),['podman','save','-o',str(archive),image])
 run('load-'+str(i),['kind','load','image-archive','--name',rec['cluster'],str(archive)])
run('helm-render',['helm','template','higress','helm/core','-n','higress-system','--create-namespace','--values',str(out/'values.yaml')],stdout=out/'manifest.yaml')
run('namespace',['kubectl','create','namespace','higress-system'])
run('install',['kubectl','apply','-f',str(out/'manifest.yaml')])
run('base',['kubectl','apply','-f',str(out/'base-mcp-only.yaml')])
run('wait-controller',['kubectl','rollout','status','deployment/higress-controller','-n','higress-system','--timeout=180s'])
run('wait-gateway',['kubectl','rollout','status','deployment/higress-gateway','-n','higress-system','--timeout=180s'])
run('stop-before-runtime',['podman','stop','mcp-auto-followup-4685-control-plane'])
rec['pass']=True;rec['config_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'cluster.yaml',out/'values.yaml',out/'manifest.yaml',out/'base-mcp-only.yaml']}
(out/'setup-results.json').write_text(json.dumps(rec,indent=2));print('kind prepared and stopped',flush=True)
