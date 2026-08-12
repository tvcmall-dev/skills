---
name: query-tvcmall-customer-data
description: 当 Codex 需要安装或修复 tvcmall MCP 连接、配置 TVCMALL_API_KEY，或查询 TVCMall 商品、运费、订单、物流、积分及余额等只读客户数据时使用。
---

# 查询 TVCMall 客户数据

## 准备 MCP

1. 检查当前会话是否存在标识为 `tvcmall` 的 MCP dependency 及预期工具。
2. 需要安装或修复时，完整读取并执行 [references/mcp-setup.md](references/mcp-setup.md)。
3. 仅在用户确认明文存储后运行 [scripts/configure_tvcmall_mcp.py](scripts/configure_tvcmall_mcp.py)。
4. 配置完成后，要求用户重启 Codex 或开启新会话，再调用业务工具。

## 路由请求

选择工具前完整读取 [references/tool-routing.md](references/tool-routing.md)。需要确认工具输入、默认值、限制或 WebApi 参数映射时，再完整读取 [references/tool-reference.md](references/tool-reference.md)。只询问所选工具必需的参数，限制查询范围，并在满足用户请求后停止调用。

## 保护客户数据

- 所有操作保持只读。
- 不要要求用户在聊天中提供 Key，也不要从配置、日志、错误或工具输出中打印 Key。
- 不要直接调用 TVCMall WebApi 或绕过 MCP 授权。
- 先给出直接答案，再提供最少且有用的结构化详情。
