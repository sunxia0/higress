Reviewed base `a42482341eb199b2c1553a560c81137ebad14441` → HEAD `06f864dc1eba5fbb8bf42a54c938c74abcb4ee88`.

**Zero P0/P1 findings. No actionable P2 findings. Both original P2 findings are resolved.**

- **Session ownership:** `runtime-verification/verify_auto.py:36` checks exact request/session ownership, credentials, four-stage sequence, and one business execution. The concurrent legacy case at `:161` requires both requests to reach the initialized barrier before business. `auto_self_test.py:67` sends swapped sessions and an extra business request through HTTP, and requires this same checker to reject them.
- **SDK error oracle:** Both clients now require JSON-RPC `-32020`. `interop/check_probe.py:36` independently checks HTTP 400, matching request ID, and the sticky fixture verdict. `interop/host/main_test.go:85` induces a real extra `tools/call` hostcall from the unchanged plugin, verifies its rejection, restores the normal fixture, then requires the same checker used by `run.sh` to continue failing because the earlier fixture failure remains recorded.

Read-only inspection; no test execution or provider actions. `git diff --check` passed.
