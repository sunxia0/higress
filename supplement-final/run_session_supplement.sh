#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export MCP_EXPECTED_SOURCE_SHA=${MCP_EXPECTED_SOURCE_SHA:?set exact final candidate SHA}
MCP_SUPPLEMENT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MCP_EVIDENCE_ROOT=$(dirname "$MCP_SUPPLEMENT_DIR")
MCP_REPO=${MCP_REPO:-/Users/xiao/.codex/worktrees/8e59/higress-fork}
MCP_ORIGINAL_RUNTIME=${MCP_ORIGINAL_RUNTIME:-$MCP_EVIDENCE_ROOT/candidate-final-e/runtime}
MCP_D_WASM=${MCP_D_WASM:-$MCP_EVIDENCE_ROOT/candidate-final-d/plugin.wasm}
MCP_HARNESS_DIR="$MCP_REPO/plugins/wasm-go/extensions/mcp-server/testdata/runtime-verification"
export MCP_SUPPLEMENT_DIR MCP_REPO MCP_ORIGINAL_RUNTIME MCP_D_WASM MCP_HARNESS_DIR
export RUNTIME_EVIDENCE=${MCP_SUPPLEMENT_SESSION_EVIDENCE:-$MCP_SUPPLEMENT_DIR/session-runtime}
export COMPOSE_PROJECT_NAME="mcp-auto-session-supplement-$$"
# An independent project/evidence directory cannot modify the original E bundle.
python3 - <<'PY'
import hashlib,json,os,subprocess
from pathlib import Path
repo=Path(os.environ['MCP_REPO']); old=Path(os.environ['MCP_ORIGINAL_RUNTIME']); out=Path(os.environ['RUNTIME_EVIDENCE'])
expected=os.environ['MCP_EXPECTED_SOURCE_SHA']
assert len(expected)==40 and all(char in '0123456789abcdef' for char in expected)
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==expected
assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
assert (old/'cleanup-proof.txt').read_text().startswith('PASS no containers remain'), 'wait for original runtime cleanup'
assert not out.exists() or not any(out.iterdir()), 'supplement evidence must be fresh'
out.mkdir(parents=True,exist_ok=True)
wasm=Path(os.environ['MCP_D_WASM']).read_bytes(); config=(old/'envoy.yaml').read_bytes()
original=json.loads((old/'manifest.json').read_text())
assert original['source_sha']==expected, 'original E source does not match the final candidate'
d_results=json.loads((Path(os.environ['MCP_D_WASM']).parent/'results.json').read_text())
assert d_results['source_sha']==expected, 'D source does not match the final candidate'
assert hashlib.sha256(wasm).hexdigest()==original['plugin_sha256'], 'D and original E Wasm hashes differ'
(out/'plugin.wasm').write_bytes(wasm); (out/'envoy.yaml').write_bytes(config)
identity={'sourceSha':original['source_sha'],'pluginSha256':hashlib.sha256(wasm).hexdigest(),
          'envoyConfigSha256':hashlib.sha256(config).hexdigest(),'originalEvidence':str(old),
          'supplementScripts':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(os.environ['MCP_SUPPLEMENT_DIR']).iterdir() if p.is_file()}}
(out/'identity.json').write_text(json.dumps(identity,indent=2,sort_keys=True)+'\n')
PY
compose() { podman compose -f "$MCP_HARNESS_DIR/compose.yaml" -f "$MCP_SUPPLEMENT_DIR/compose.override.yaml" "$@"; }
cleanup() { compose --profile verify down --volumes --remove-orphans >"$RUNTIME_EVIDENCE/cleanup.log" 2>&1 || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
compose --profile verify config --format json >"$RUNTIME_EVIDENCE/compose-config.json"
podman image inspect higress-registry.cn-hangzhou.cr.aliyuncs.com/higress/gateway:v2.2.3 docker.io/library/python:3.12-alpine --format '{{json .RepoDigests}}' >"$RUNTIME_EVIDENCE/image-digests.jsonl"
compose up -d backend-primary backend-secondary gateway
verify_status=0
compose --profile verify run --rm --no-deps verifier >"$RUNTIME_EVIDENCE/verifier.log" 2>&1 || verify_status=$?
compose stop gateway
container_id=$(compose ps -a -q gateway)
test "$(podman inspect --format '{{.State.Running}}' "$container_id")" = false
compose logs --no-color gateway >"$RUNTIME_EVIDENCE/gateway.log"
compose logs --no-color backend-primary >"$RUNTIME_EVIDENCE/backend.log"
cleanup
trap - EXIT INT TERM
if test -z "$(podman ps -a --filter "label=com.docker.compose.project=$COMPOSE_PROJECT_NAME" --format '{{.ID}}')"; then
  echo "PASS no containers remain for compose project $COMPOSE_PROJECT_NAME" >"$RUNTIME_EVIDENCE/cleanup-proof.txt"
else
  echo "FAIL containers remain for compose project $COMPOSE_PROJECT_NAME" >"$RUNTIME_EVIDENCE/cleanup-proof.txt"
fi
python3 "$MCP_SUPPLEMENT_DIR/finalize_session.py"
exit "$verify_status"
