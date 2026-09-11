# mcp-server opt-in auto protocol: verification evidence

Source: `3966c7e6c189fa1007fdca0386ad9a8f4291e953`, compared with `dc0999326b1a8df4269c13d0cf6ee2b725259f6e`.
Planning: [Proposal #4683](https://github.com/higress-group/higress/issues/4683), [Design #4684](https://github.com/higress-group/higress/issues/4684).

This separate evidence branch contains text/JSON/configuration/logs, not a product change. Use a commit-pinned link for immutable evidence. No kubeconfig, private key, native executable, container archive, or Wasm binary is published. Binary hashes remain in the manifests. Synthetic fixture credentials in source-derived configs are not live credentials.

| Layer | Actual outcome | Evidence |
|---|---|---|
| Pre-change real Envoy | 26 PASS / 0 FAIL, 55/55 access records, cleanup PASS | [baseline](baseline-runtime/manifest.json) |
| Pre-change kind target | Original five assertions PASS | [result](kind/baseline-conformance-result.json) |
| Candidate package/race/extension/SDK/Wasm | All five commands exit 0, clean unchanged source | [commands, times, hashes](candidate-3966c7e6-d/results.json) |
| Candidate real Envoy | 68 PASS / 0 FAIL, main expected set 50 cases, 112/112 access records, cleanup PASS | [manifest](candidate-3966c7e6-e/runtime/manifest.json), [matrix](candidate-3966c7e6-e/runtime/matrix.json), [command](candidate-3966c7e6-e/result.json) |
| Candidate kind target | Seven exact MCP assertions PASS | [result](candidate-3966c7e6-kind/results.json), [log](candidate-3966c7e6-kind/conformance.log) |
| Concurrent legacy sessions | Two identities overlap at initialize barrier; each has four calls, exact matching session and one business execution | [events and swapped-session negative controls](supplement/session-runtime/session-isolation.json), [manifest and cleanup](supplement/session-runtime/manifest.json) |
| SDK negative fixture companion | Original HTTP400/-32020 accepted; injected fixture sequence HTTP500 rejected (checker exit42) | [strict raw HTTP companion](supplement/probe-oracle/probe-oracle-summary.json) |
| Independent exact-head review | Zero P0/P1; two non-blocking P2 test-oracle follow-ups remain in source | [review](review-3966c7e6.md) |

Candidate Wasm SHA-256: `a7f9dbc38a6789249bd2ee9e1bb5a7bc20c31b6710eed8d02a14623fec5f0fc9`.
Gateway v2.2.3 digest includes `sha256:2b00548e16aafc5ee51314a0de8c4df4369877b1d0f9eaec13becc3675dd04b7`; baseline and candidate use the same image. All resolved digests are in the runtime manifests.

## Reproduction and boundaries

The exact repo commands and original absolute paths are retained in result JSON files. To rerun elsewhere, check out the recorded source and adapt only workspace/evidence directory variables. `run-d.py`, `run-runtime.py`, `run-kind.py`, and [supplement instructions](supplement/README.md) show the actual orchestration. `artifact-sha256.json` hashes the published evidence files; each runtime bundle retains its unchanged original `SHA256SUMS`.

The standard `make higress-wasmplugin-test` orchestration did **not** pass on this macOS/Podman environment: it was interrupted during old kind image acquisition (exit2 from Make, underlying create-cluster130). A prior all-suite setup attempt was also interrupted during unrelated backend pulls, and host port80 forwarding failed with permission denied. The successful kind result executes the original same-source Linux arm64 conformance binary and paired manifests inside the owned kind node, using `--test-area=run` and the three unchanged prerequisite objects from baseline manifests. This proves the seven targeted assertions, not the full Make orchestration or unrelated suites. See [environment adaptation](kind/environment-adaptation.json), [Make attempt](kind/standard-make-result.json), [original adaptation note](verification-environment-note.md).

A diagnostic extension run with a deliberately shortened 90-second limit timed out while repeatedly initializing Wasm; the original complete extension command passed in 249 seconds. Its diagnostic log is retained and is not counted as a test success. An earlier worker interop run left an owned go-run child; the worker verified its PID/command/port and removed it. Final process and container checks are recorded in [cleanup](cleanup-final.json).

The two P2 observations remain applicable to committed fixtures: the runtime alias oracle cannot independently detect session swaps, and SDK negative tests accept arbitrary exceptions. The separate supplements verify exact session equality and strict raw HTTP errors on the unchanged candidate without claiming those fixture assertions were repaired. The injected SDK overlay changes only the fixture's observed-sequence record, not actual business execution. The supplemental `identity.json` captures a broad input directory, including an initially empty growing command log; the final published bytes are authoritatively hashed by `artifact-sha256.json` and supplemental `SHA256SUMS`.

Default legacy, opt-in auto only, no cache, no cross-request session reuse, no business replay, no mixed-protocol pool guarantee, no recall of an already submitted hostcall, and no #4597 routing fix. Deployment, release image publication, human approval and merge are not claimed.
