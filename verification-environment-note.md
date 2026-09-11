实施验证环境补充（保持功能契约及 V1–V8 验收范围）：

- 已完成功能基线 `dc0999326b1a8df4269c13d0cf6ee2b725259f6e` 的既有真实 Envoy harness：26 PASS / 0 FAIL，access coverage 与 cleanup PASS；Wasm SHA-256 `536c5b75b75f27e26a6e154e9ef9c3d6a86e60896c6d619ce61a426358a149ec`。候选结果尚未在此宣称完成。
- 本机为 macOS arm64，Go 1.26.0、Node 22.19.0、Podman client 6.0.2 / server 5.8.5；独立 kind v0.32.0 / Kubernetes v1.32.2。无 Docker CLI，本机监听 80 端口返回 permission denied。
- 因此 kind 采用同源 `go test -c` 生成的 Linux/arm64 conformance 二进制，在独立 kind 节点内以 `localhost:80` 运行原测试。使用已有 `--test-area=run --execute-tests=WasmPluginsMCP20260728` 入口，准备原 base manifests 中该用例需要的 Namespace/Service/Deployment，并由测试原样应用成对的 MCP manifest。原 `--test-area=all` 准备无关后端时停在镜像拉取，已中止并保留失败历史，未计为通过。
- 基线原有 5 个 MCP 断言已在该执行方式下全部通过。候选将按同样方式运行扩展后的用例。gateway/controller/pilot 固定为 v2.2.3；网关镜像 ID `e0732a66b9152c10acb0710d07c4ebec5e719f72bd62bd8112662ed38f4f9265`，其已解析 digest 和候选源/测试二进制/Wasm 身份将在 TASK E 最终证据中记录。此执行适配不覆盖或宣称整个仓库通用 conformance setup 已通过。
- 本地 Go 测试依赖由当前仓库 gitlink 的精确提交归档至 ignored `external/`，未修改依赖源码或 root go.mod。kind 和重型 runtime 阶段顺序执行，避免 4 GiB Podman VM 内存竞争。
- 另核对当前 `tools/hack/build-wasm-plugins.sh` 已按 release catalog 选择批量构建插件，Design/AGENTS 中仅由 `-alpha` 触发构建的描述已滞后。本次仍使用候选 `2.0.3-alpha`；registry 查询明确返回 manifest unknown，未复用已有镜像版本。

这是执行环境与证据边界的记录，不构成 maintainer approval、完成验收或合并声明。最终命令、退出码、完整矩阵及不可变证据链接将回填 TASK D/E。
