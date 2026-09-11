# Design #4684 implementation and verification

Exact candidate: `3966c7e6c189fa1007fdca0386ad9a8f4291e953`; pre-change functional baseline: `dc0999326b1a8df4269c13d0cf6ee2b725259f6e`. Clean tracked tree throughout final D/E. Signed-off implementation commits: A `620dbe39c4412953ac83a4b7b90480d3ac3f1a73`, B `f3ccbe7e84551968f28b655382bc624821617e47`, classifier correction `488d81a35d217571a105b1bf3aa3e7cfa51a6f20`, C `3966c7e6c189fa1007fdca0386ad9a8f4291e953`.

## SPEC and Design verification coverage

| SPEC / Design group | Implementation and actual evidence |
|---|---|
| SPEC-4683001 / V1 | auto enum and auto+HTTP probe-timeout validation; legacy defaults/Clone/eligibility. Package tests, extension Go/Wasm tests, independent old Wasm rejecting auto, unknown-enum negative, five explicit/default baseline comparisons. |
| SPEC-4683002 / V2 | Request-local exchange and fresh discovery. Real modern 2-call / legacy 4-call sequences, direct call, modern→legacy→modern capability changes, four concurrent modern requests, local discover and allowTools zero-upstream checks, two concurrent legacy requests in supplement. |
| SPEC-4683003 / V3 | Strict probe classifier. Pure classifier tables plus actual HTTP401/403/429/5xx/redirect, modern error, supported/unknown/conflicting versions, ordinary400/404/405, malformed/trailing/batch/wrong-ID tests. Business count zero on rejected probes. |
| SPEC-4683004 / V4 | Auto-specific strict JSON/SSE and initialize/initialized handling. Raw numeric/opaque preservation, version checks, notifications, duplicate/missing SSE final frames, pre-copy1MiB limit, invalid initialize and failed notification. |
| SPEC-4683005 / V5 | Prepared target/auth snapshot and operation-specific headers. Target/authority and auth aliases in actual backend events; fixed/server/tool/passthrough policies; no session on probe; exact same-request session booleans on initialized/business in concurrent legacy supplement. |
| SPEC-4683006 / V6 | Irreversible phase terminal and one business dispatch. Unit race/callback/submit-failure tests, actual backend-exec-then-response-loss count1, business-version error without replay, four cancellation stage barriers, backend-returned/upstream/downstream gauge and listener-fence evidence. |
| SPEC-4683007 / V7–V8 | Pinned Go SDK1.7.0 and TS2.0.0 clients PASS; strict raw HTTP companion with negative fixture oracle; bilingual config/limitations/rollback docs and standalone sample; 2.0.3-alpha unused registry tag; CI path/build checks; same Wasm on real Envoy and seven kind assertions. |

## Actual results

- Final D: package, race, extension, SDK interop and Wasm build commands all exit0. Exact commands, timestamps, log hashes and toolchains: `candidate-3966c7e6-d/results.json`.
- Final E: runtime command exit0; expected main set50 cases, aggregate68 PASS/0 FAIL; access ledger112/112 with no missing/duplicate/unexpected IDs; cleanup PASS. `candidate-3966c7e6-e/result.json` and `runtime/manifest.json`.
- Baseline: real Envoy26 PASS/0 FAIL, access55/55, cleanup PASS; original five kind assertions PASS.
- Candidate kind: original same-source conformance binary executes all seven targeted assertions; no target skipped. `candidate-3966c7e6-kind/results.json`.
- Supplement: true overlapping Alice/Bob legacy sessions, eight upstream events, exact session comparison booleans, each backend execution1, two access records, swapped-session oracle negatives rejected, cleanup PASS. Unchanged candidate Wasm/config hashes checked.
- SDK strict companion: unchanged fixture HTTP400/-32020+matching ID accepted; synthetic extra observed business record causes real fixture500 and checker exit42; both native hosts exited. This does not claim an injected real extra business call or a source fix for SDK catch assertions.

Wasm SHA-256: `a7f9dbc38a6789249bd2ee9e1bb5a7bc20c31b6710eed8d02a14623fec5f0fc9`. Gateway v2.2.3 resolved digests are identical across functional baseline/candidate phases. Go1.26.0 darwin/arm64, Node22.19.0, Podman6.0.2 client, kind0.32.0, Kubernetes1.32.2; original conformance binary cross-compiled Linux arm64 with source gitlinks extracted exactly for ignored external dependencies.

## Limits and retained failures

The full Make wrapper was attempted and did not pass: interrupted old kind image acquisition; prior all-suite bootstrap also stopped during unrelated pulls, and macOS host80 forwarding failed. The recorded alternative executes the original seven target assertions inside kind; it does not validate all Make orchestration or unrelated suites. A separate90-second extension diagnostic timed out; the complete extension suite passed with its normal timeout. Failure logs and cleanup records are retained.

Independent reviewer on exact base/head returned zero P0/P1 and two non-blocking P2 fixture improvements. Both remain applicable to committed tests and are published unchanged; the supplements address the present verification evidence without claiming fixture repairs. No approval/merge claim. Default legacy, opt-in auto, no cache or cross-request session reuse, no business replay; existing #4597 final dispatch behavior remains outside scope.
