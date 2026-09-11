# Design #4684 verification supplement at the exact final candidate HEAD

This directory is outside the worktree. It supplements TASK E evidence and does not
resolve or modify the two non-blocking P2 review findings in candidate source.
The caller supplies the exact final candidate SHA. Each runner checks the clean
checkout against it; the runtime runner also requires D and original E source
identities and Wasm hashes to match. Original `supplement/` evidence is retained.

## Concurrent legacy identity/session evidence

The original backend aliases every `auto-session-*` as `current`. That proves
presence but cannot identify Alice/Bob session swaps. `session_backend.py` imports
the candidate's original backend and adds **only backend verification fields**:
`requestSessionMatches` compares the complete incoming session to the session
issued for the current `requestKey`, in backend memory; output contains booleans
and public aliases. Sessions are never published in supplement evidence.

`verify_session.py` sends concurrent Alice and Bob legacy calls to the candidate's
existing passthrough listener, requires both initialize calls to reach the same
barrier before release, then verifies each identity has exactly discover →
initialize → initialized → tools/call, the right auth alias on all four calls,
no early session, exact session equality for initialized/business, and one actual
backend execution. Its negative oracle swaps the complete sessions in memory for
each of those phases and must reject both variants.

Wait until the original runtime finishes and its cleanup proof exists. Then run:

```bash
MCP_EXPECTED_SOURCE_SHA=53587de46153829d05130649aa132e45885c77f6 \
MCP_REPO=/Users/xiao/.codex/worktrees/8e59/higress-fork \
  bash /Users/xiao/.codex/worktrees/8e59/higress-mcp-auto-tuaqf6zu/supplement-final/run_session_supplement.sh
```

The runner checks clean exact HEAD and original cleanup proof, copies the original
candidate `envoy.yaml` and TASK D `plugin.wasm` into a **fresh supplement evidence
directory**, verifies the Wasm hash matches original E, and starts only the two
original Compose backends and candidate gateway. The second backend is retained
because the unchanged gateway config includes its cluster. A Compose override
mounts this directory read-only and starts the primary backend wrapper. The one
verifier container executes `verify_session.py`; no `podman cp` is necessary.

It uses its own Compose project, stops and inspects the gateway before log capture,
removes that project's containers, checks exact access coverage for the two
requests, and writes `session-runtime/manifest.json` and `SHA256SUMS`. The original
E directory is never written. Do not rerun into the same evidence directory;
set `MCP_SUPPLEMENT_SESSION_EVIDENCE` to another fresh external path when necessary.
Defaults are `candidate-final-e/runtime`, `candidate-final-d/plugin.wasm` and
`supplement-final/session-runtime`. Input paths can be overridden with
`MCP_ORIGINAL_RUNTIME` and `MCP_D_WASM`; D `results.json` must sit beside its Wasm.

Local oracle-only self-test, without Envoy:

```bash
MCP_HARNESS_DIR=/Users/xiao/.codex/worktrees/8e59/higress-fork/plugins/wasm-go/extensions/mcp-server/testdata/runtime-verification \
  PYTHONDONTWRITEBYTECODE=1 python3 /Users/xiao/.codex/worktrees/8e59/higress-mcp-auto-tuaqf6zu/supplement-final/verify_session.py --self-test
```

This supplements one exact endpoint, two concurrent credentials, and request-scoped
sessions. It does not prove protocol-consistent upstream pools or a cache, and it
does not change the original runtime harness's weak alias assertion.

## SDK probe-error strict raw HTTP companion

The unchanged SDK clients treat an arbitrary error as success in their negative
scenario. The independent `raw_probe_oracle.py` requires HTTP 400, RPC -32020,
matching business ID, JSON-RPC 2.0 and absence of result. Any other response is exit
42; checker failures are exit 3 and cannot satisfy the negative oracle.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  /Users/xiao/.codex/worktrees/8e59/higress-mcp-auto-tuaqf6zu/supplement-final/run_probe_supplement.py \
  --repo /Users/xiao/.codex/worktrees/8e59/higress-fork \
  --source 53587de46153829d05130649aa132e45885c77f6 \
  --out /Users/xiao/.codex/worktrees/8e59/higress-mcp-auto-tuaqf6zu/supplement-final/probe-oracle-fresh
```

The runner builds and directly executes the unchanged native interop TestHost
binary and proves the real raw response is 400/-32020. It separately builds an
external `go build -overlay` fixture variant that injects a synthetic extra
`tools/call` record into the existing sequence oracle. That variant follows the
fixture's real HTTP 500 failure path, and the strict checker must reject it with
exit 42. It also checks the HTTP500 body identifies the expected sequence failure,
so a generic harness/build failure cannot masquerade as the intended negative.
The source file is hash-checked before and after; candidate Git status stays clean.

The overlay changes only the fixture's observed-sequence ledger; **it does not
execute an extra business request**. This proves the independent checker refuses
the previously swallowable fixture HTTP500, not that SDK typed error assertions
were corrected. Existing TASK D official SDK evidence remains separate. Both
native hosts are executed directly (no `go run` parent) and reaped after each phase.

The earlier candidate's independent companion result remains in
`../supplement/probe-oracle/`. It is historical evidence only. Run the final
companion anew at the supplied final SHA; this directory contains no copied
historical results and does not claim the final run has passed.
