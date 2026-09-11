准确评审 head：f3ccbe7e84551968f28b655382bc624821617e47

[P2] 普通 HTTP 回退分支仍会接受明确 modern 错误和损坏的 RPC 报文

位置：plugins/wasm-go/pkg/mcp/server/proxy_response.go:442-451。例如 discover 返回 HTTP 400、MCP-Protocol-Version: 2026-07-28 和 ID 匹配的 -32602 错误时，decodeAutoResponse 成功，但该分支没有检查 autoModernEvidence，直接开始 legacy initialize。另一个确定触发是 HTTP 400/404 的 JSON-RPC -32601 响应后追加 {}：解码失败被统一归为 invalid_json，gjson.ValidBytes 又为 false，因此仍允许回退；batch RPC 同样会漏过这个判断。两类响应都不满足 Design 的“无可识别 modern 错误的普通 HTTP 候选”及严格单对象 framing 契约；若随后 legacy 握手成功，业务会在本应终止的探测后执行。建议在通用回退之前拒绝明确 modern 证据，并区分普通 HTML/空响应与 batch、trailing JSON 等损坏的 MCP 报文，补充零后续 callout 的回归用例。
