# TVCMall MCP 配置

## 配置判断

1. 检查当前会话是否存在 `tvcmall` MCP 依赖及预期工具。
2. 如果存在，先调用 `tvcmall_auth_status`，不要自动重复安装。
3. 如果不存在，说明安装会按照 [TVCMall MCP](https://github.com/tvcmall-dev/mcp) 的接入方式，把远程 MCP 连接注册到用户的 Codex 配置；不要克隆、构建或启动服务端仓库。

## API Key

- 询问用户是否已有 `TVCMALL_API_KEY`。
- 如果没有，引导用户前往 https://www.tvcmall.com/user/agentkeys 登录并申请，然后暂停配置，等待用户取得 Key。
- 不要求用户把 Key 粘贴到聊天中。
- 如果用户已经在聊天中发送了 Key，不要复述或继续使用该值；说明它已暴露，引导用户立即撤销并申请新 Key，然后只通过终端无回显输入配置新 Key。
- 说明用户已选择将 Key 明文保存在用户级 Codex `config.toml` 中。
- 只接受完整的个人 PAT，格式为 `tmcp_v1_{tokenId}.{secret}`；不要添加 `Bearer ` 前缀。

## 配置

获得用户明确确认后，在本 Skill 目录运行：

```powershell
python scripts/configure_tvcmall_mcp.py
```

脚本通过终端无回显输入读取 Key，并写入：

```toml
[mcp_servers.tvcmall]
url = "https://mcpserver.tvc-mall.com"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

不要把 Key 作为命令行参数。不要给 endpoint 追加 `/mcp`。脚本会保留其他 Codex 设置和 MCP Server，拒绝覆盖无效 TOML，并在替换现有有效配置前创建备份。

## 重启与验证

要求用户重启 Codex 或新建会话。确认 `tvcmall` 工具可见后调用 `tvcmall_auth_status`。`configured: true` 仅说明当前 MCP session 已加载 PAT；通过用户请求的只读业务查询验证相应权限。

## 配置错误

- TOML 无效或写入失败：保留原始配置，报告非敏感错误和备份路径。
- 网络错误或 `5xx`：保留 HTTPS 配置，说明标准服务暂时不可用并建议稍后重试。
- 不回退到 HTTP，不改用旧 endpoint，也不自动追加路径。
