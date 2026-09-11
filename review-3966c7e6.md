Reviewed base: dc0999326b1a8df4269c13d0cf6ee2b725259f6e
Reviewed head: 3966c7e6c189fa1007fdca0386ad9a8f4291e953
Independent read-only reviewer: mcp_auto_review (not a code writer).
No P0/P1. Prior malformed modern/trailing/batch fallback finding was corrected in 488d81a3.

1. **[P2] Session 隔离 oracle 无法识别跨请求串用**
   `plugins/wasm-go/extensions/mcp-server/testdata/runtime-verification/auto_backend.py:57` 把所有 `auto-session-*` 都记为 "current"；`verify_auto.py:142` 仅检查这个标记。例如 Bob 的 initialized 和业务错误携带 `auto-session-alice`，该场景仍会 PASS。并发场景目前只运行不含 session 的 modern，无法补足这一缺口。应记录不含实际 session 的“是否匹配当前 requestKey”布尔值，断言后续 legacy 阶段精确匹配；增加不同凭证、独立 session 的并发 legacy 请求及交换 session 的负向 oracle 自测，落实 Design V5/V6。

2. **[P2] SDK 负向场景把 fixture 自身失败也算预期成功**
   `plugins/wasm-go/extensions/mcp-server/testdata/interop/go-client/main.go:65-69`，同类问题在 `typescript/client.mjs:41-47`。两端只要求调用抛出任意错误。但 host 检测到多发业务等非法序列时，会在 `host/main.go:151-153` 返回 HTTP 500；SDK 随即把该错误视为“探测失败、业务未派发”的 PASS。因此新增的 sequence oracle 恰好在负向用例中不能阻止误通过。应校验预期的 `-32020`/HTTP 400，并将 fixture 序列失败作为独立且不可被客户端预期错误吞掉的整体失败；补充额外业务 callout 的负向自测。
