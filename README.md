# MCP auto protocol follow-up verification

PR [#4685](https://github.com/higress-group/higress/pull/4685), Proposal [#4683](https://github.com/higress-group/higress/issues/4683), Design [#4684](https://github.com/higress-group/higress/issues/4684).
Final source: `06f864dc1eba5fbb8bf42a54c938c74abcb4ee88`; merged main: `a42482341eb199b2c1553a560c81137ebad14441`; test fix: `9113d0469393df84bb04801176c44492e6e58975`. TASK-4684006/007 record this follow-up. Earlier A–E evidence remains at [9ac39019](https://github.com/sunxia0/higress/tree/9ac39019c0fe7be855a14aca1a3725c7a05e4ae1).

## Changes and verification

The production MCP source is unchanged. Tracked tests now check exact request-owned sessions with safe booleans, actual concurrent legacy initialized barriers, swapped sessions and repeated business execution. Both SDK clients require the expected -32020 error; an independent raw checker requires HTTP400, matching JSON-RPC ID and zero sticky fixture failures. A negative host test induces an actual extra business callout from the unchanged plugin and requires this same checker to reject it after a later valid response. The interop launcher reaps its actual host binary.

- [Final native tests/build](final-d/results.json): ten commands exit0 (fixture/lifecycle self-tests, release fixture/catalog, MCP package/race/extension, SDK interoperability and Wasm build). [Final host race](final-host-race.json) also exit0. [Worker focused results](worker/results.json) belong to the test-fix commit, distinct from final integrated-head results.
- [Full real Envoy matrix](final-e/runtime/matrix.json): 69 PASS / 0 FAIL, main expected set51, auto main cases40. [Access coverage](final-e/runtime/access-coverage.json): 114/114, no missing, duplicate or unexpected records. [Source/image/config/hash/cleanup manifest](final-e/runtime/manifest.json), [exact command](final-e/result.json).
- [kind targeted conformance](final-kind-rerun/results.json): original seven assertions7/7, exact-source Linux arm64 runner and the same final Wasm. [Conformance log](final-kind-rerun/conformance.log).
- [Independent review](review-final.md): zero P0/P1, no actionable P2, both previous P2 findings resolved. This is agent review context, not maintainer approval.
- [Final GitHub checks](ci-final.json): all reported checks pass or are explicitly skipped; [workflow status](ci-final-runs.json).
- [Cleanup](cleanup-final.json): owned runtime resources, cluster, build artifact and VM lifecycle checked.
- [Identity](identity-final.json): sunxia0/admin, matching PR author; GH_TOKEN and GITHUB_TOKEN unset for identity and verification commands.

Wasm SHA256: `a7f9dbc38a6789249bd2ee9e1bb5a7bc20c31b6710eed8d02a14623fec5f0fc9`. This equals the preceding feature's artifact because this follow-up changes only tests and integrates unrelated main changes.

## Boundaries and retained failures

Real Envoy uses the Design's fixed v2.2.3 gateway image and records its resolved digest. Local kind uses the prior documented macOS/Podman adaptation: unchanged paired manifests and seven target assertions run inside the owned node; this is not a claim that the local standard Make wrapper passed. GitHub full suite results are listed separately.

The first kind template apply failed because repository CRDs had not yet been installed. [Initial setup record](kind/setup-results.json) and its install log remain unchanged. [Recovery](kind/setup-recovery-results.json) installs those CRDs and reapplies the same template before waiting for both deployments. This is environment preparation, not a product fix or a suppressed test failure. The first kind invocation after restarting its node also hit a transient Kubernetes authorization failure before executing any conformance assertion; final-kind/results.json retains that failure, and final-kind-rerun/results.json records the successful rerun after the API/deployment readiness gate. A generated retry-helper syntax error was corrected before any verification command ran and is retained in kind-retry-preflight-error.log.

The first two full GitHub plugin e2e attempts failed before MCP assertions because registry authentication connections reset while pulling unrelated Dubbo (attempt1/Go) and Nacos (attempt2/Rust) fixture images; their in-job retries then failed on root-owned pilot build artifacts. A selected Go retry (attempt3) was cancelled immediately against the inherited failed Rust matrix state and executed no test steps. Attempt4 reran the full Go/Rust matrix on fresh runners without source changes and passed both jobs, including all seven MCP20260728 target assertions. The final status is reported above; ci-retry.json and ci-plugins-attempt*.log preserve the exact attempts. The same failure chain was already present on current main a4248234 in [run35598586052](https://github.com/higress-group/higress/actions/runs/35598586052) on September21; ci-upstream-main-failure.log is retained. These infrastructure failures do not constitute a passing full-suite result.

Historical failures and supplemental scripts remain in earlier immutable evidence. They are not relabeled as new-head results. Binaries, archives and kubeconfig/private credentials are omitted here; their hashes remain in command manifests. Synthetic public fixture identities are safe test data. Files in this publication are indexed in `artifact-sha256.json`. No maintainer approval, deployment or merge is claimed.
