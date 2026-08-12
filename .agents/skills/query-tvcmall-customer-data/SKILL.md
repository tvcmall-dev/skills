---
name: query-tvcmall-customer-data
description: Configure and use the TVCMall Customer MCP for read-only product, shipping, order, tracking, points, and balance queries. Use when Codex needs to install or repair the tvcmall MCP connection, configure TVCMALL_API_KEY, or answer TVCMall customer-data questions.
---

# TVCMall 客户数据查询

## 准备 MCP

1. 检查是否存在标识为 `tvcmall` 的 MCP 依赖及预期工具。
2. 如需安装或修复，完整阅读并遵循 [references/mcp-setup.md](references/mcp-setup.md)。
3. 仅在用户确认明文保存后运行 [scripts/configure_tvcmall_mcp.py](scripts/configure_tvcmall_mcp.py)。
4. 配置完成后，要求用户重启 Codex 或新建会话，再调用业务工具。

## 路由请求

选择工具前完整阅读 [references/tool-routing.md](references/tool-routing.md)。只追问所选工具的必需参数，使用有限查询，并在满足用户请求后停止。

## 保护客户数据

- 所有操作保持只读。
- 不要求用户在聊天中提供 Key，也不从配置、日志、错误或工具输出中打印 Key。
- 不直接调用 TVCMall WebApi，也不绕过 MCP 授权。
- 先给出直接答案，再提供最少且有用的结构化明细。
