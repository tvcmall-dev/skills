# TVCMall Skills

面向 TVCMall 业务场景的 Codex Skills 集合。当前 Skill 通过 TVCMall Customer MCP 提供只读客户数据查询，并在首次使用时引导完成 MCP 连接和个人 API Key 配置。

## Skills

| Skill | 功能 |
| --- | --- |
| `query-tvcmall-customer-data` | 商品、未下单运费、订单、物流、积分和余额查询；首次使用时引导配置 MCP |

## 环境要求

- Codex CLI、IDE extension 或 desktop app；
- Python 3.11 或更高版本；
- 个人 `TVCMALL_API_KEY`。

## 安装与发现

```powershell
git clone https://github.com/tvcmall-dev/skills.git
cd skills
codex
```

从仓库目录启动 Codex 后，Codex 会发现 `.agents/skills` 下的仓库级 Skill。不需要克隆、构建或运行 TVCMall MCP Server；Skill 连接远程 Streamable HTTP MCP。

## 首次配置

TVCMall MCP 的标准 endpoint 是 `https://mcpserver.tvc-mall.com`。

1. 在 Codex 中调用 `$query-tvcmall-customer-data` 或提出 TVCMall 查询。
2. Skill 检查 `tvcmall` MCP 是否已经可用。
3. 如果没有安装，Skill 按 [TVCMall MCP](https://github.com/tvcmall-dev/mcp) 的接入说明注册远程连接，不在本地运行 MCP Server。
4. 如果没有个人 `TVCMALL_API_KEY`，先前往 https://www.tvcmall.com/user/agentkeys 申请。
5. 确认明文保存后，本机脚本使用终端无回显输入读取 Key，并更新 Codex 用户级 `config.toml`。
6. 重启 Codex 或新建会话，再检查 `tvcmall` tools。

配置结果如下。`<TVCMALL_PAT>` 仅为占位符：

```toml
[mcp_servers.tvcmall]
url = "https://mcpserver.tvc-mall.com"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

Key 会按照当前设计明文保存在用户级 Codex 配置中。Windows 默认路径为 `%USERPROFILE%\.codex\config.toml`；macOS 和 Linux 默认为 `~/.codex/config.toml`。如设置了 `CODEX_HOME`，则使用其中的 `config.toml`。

## 使用示例

```text
使用 $query-tvcmall-customer-data 查询我最近 10 个订单。
搜索 SKU 为 100001234A 的商品并查看详情。
估算 2 件该商品寄往美国的运费。
查询最近已发货订单的物流状态。
查询我的积分汇总和最近积分流水。
查询最近的余额支出记录。
```

当前能力只读，包括商品、未下单商品运费、订单、物流、积分和余额流水。不支持下单、支付、取消订单、修改地址、积分兑换或文件导出。

## 安全

- 不要把真实 `TVCMALL_API_KEY` 提交到 Git、粘贴到聊天、放进命令参数、日志或截图。
- `TVCMALL_API_KEY` 使用完整个人 PAT，不添加 `Bearer ` 前缀。
- 不要为入站 MCP 连接配置 `Authorization` Header。
- 每位用户使用自己的 Key，不要使用网站密码、网站登录 token、OAuth token 或共享凭据。
- 不要尝试恢复服务端已脱敏的客户信息。
- endpoint 必须保持为标准 HTTPS 地址；连接失败时不要回退到 HTTP，也不要追加 `/mcp`。

## 验证

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
python -m unittest discover -s tests -v
rg -n -F 'https://mcpserver.tvc-mall.com' README.md .agents\skills\query-tvcmall-customer-data
git diff --check
```

## 贡献

新增或修改 Skill 时：

1. 遵循标准 `SKILL.md`、`agents/openai.yaml`、`scripts/` 和 `references/` 结构；
2. 为脚本和 Skill 合约补充测试；
3. 更新本 README 的 Skills 表；
4. 确保真实凭据与客户数据不进入仓库；
5. 提交前运行完整验证。

## 相关链接

- [TVCMall MCP](https://github.com/tvcmall-dev/mcp)
- [申请 TVCMALL_API_KEY](https://www.tvcmall.com/user/agentkeys)
- [OpenAI Skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI MCP](https://learn.chatgpt.com/docs/extend/mcp)
