# TVCMall MCP 配置

## 判断配置状态

1. 检查当前会话是否存在 `tvcmall` MCP dependency 及预期工具。
2. 如果存在，先调用 `tvcmall_auth_status`，不要自动重复安装。
3. 如果不存在，说明安装遵循 [TVCMall MCP](https://github.com/tvcmall-dev/mcp) 的远程连接方式，并在用户的 Codex 配置中注册 MCP。不要克隆、构建或启动 Server 仓库。

## API Key

- 询问用户是否已有 `TVCMALL_API_KEY`。
- 如没有，引导用户前往 https://www.tvcmall.com/user/agentkeys 登录并申请；在用户取得 Key 前暂停配置。
- 不要要求用户把 Key 粘贴到聊天中。
- 如果用户已在聊天中发送 Key，不要重复该 Key，也不要继续使用该值。说明凭据已经暴露，引导用户立即撤销并申请新 Key，然后只通过关闭输入回显的终端提示配置新 Key。
- 说明用户选择把 Key 明文存储在用户级 Codex `config.toml` 中。
- 只接受格式为 `tmcp_v1_{tokenId}.{secret}` 的完整个人 PAT，不要添加 `Bearer ` 前缀。

## 写入配置

用户明确确认后，从 Skill 目录运行：

```powershell
python scripts/configure_tvcmall_mcp.py
```

脚本通过关闭输入回显的终端提示读取 Key，并写入：

```toml
[mcp_servers.tvcmall]
url = "https://openapi.tvc-mall.com/mcp"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

不要通过命令行参数传递 Key。`/mcp` 是 endpoint 的组成部分：不要删除，也不要重复追加。脚本保留其他 Codex 设置和 MCP Server；现有 TOML 无效时拒绝覆盖；替换有效配置前创建备份。脚本运行时，不要让其他进程编辑同一个 `config.toml`。脚本能检测替换前发生的变更并安全失败，但文件替换本身不提供跨进程锁。

## 重启与验证

要求用户重启 Codex 或开启新会话。确认 `tvcmall` 工具可见后，调用 `tvcmall_auth_status`。`configured: true` 只表示当前 MCP 会话已加载 PAT；仍需通过用户请求的只读业务查询验证对应权限。

## 配置错误

- TOML 无效或写入失败：保留原配置，只报告不含敏感信息的错误和备份路径。
- 网络错误或 `5xx`：保留规范 HTTPS 配置，说明服务可能暂时不可用并建议稍后重试。
- 不要回退到 HTTP、切换到旧 endpoint、删除 `/mcp` 或追加第二个 `/mcp`。
