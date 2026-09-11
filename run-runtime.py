import os,sys,json,subprocess,pathlib,datetime
repo=pathlib.Path('/Users/xiao/.codex/worktrees/8e59/higress-fork')
out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True)
cmd=['bash',str(repo/'plugins/wasm-go/extensions/mcp-server/testdata/runtime-verification/run.sh')]
record={'source_sha':head,'source_tree_clean':True,'command':cmd,'environment_overrides':{'RUNTIME_EVIDENCE':str(out/'runtime')},'started_at':now()}
with (out/'command.log').open('w') as log:
 result=subprocess.run(cmd,cwd=repo,env=dict(os.environ,**record['environment_overrides']),stdout=log,stderr=subprocess.STDOUT)
record.update(exit_code=result.returncode,finished_at=now(),final_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),final_status=subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True))
(out/'result.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
raise SystemExit(result.returncode)
