# TVCMall Skills

本仓库提供可复用的 TVCMall Codex Skills。当前 Skill 通过 TVCMall Customer MCP 提供只读客户数据查询，并在首次使用时引导完成 MCP 连接和个人 `TVCMALL_API_KEY` 配置。

## Skills

| Skill | 能力 |
| --- | --- |
| `query-tvcmall-customer-data` | 商品、下单前运费、订单、物流、积分和余额查询；首次使用时引导配置 MCP |

## 环境要求

- Codex CLI、IDE 扩展或桌面应用；
- Python 3.11 或更高版本；
- 个人 `TVCMALL_API_KEY`。

## 安装与发现

```powershell
git clone https://github.com/tvcmall-dev/skills.git
cd skills
codex
```

从仓库目录启动 Codex 后，会自动发现 `.agents/skills` 下的项目级 Skill。无需在本地克隆、构建或运行 TVCMall MCP Server；该 Skill 连接远程 Streamable HTTP MCP。

## 首次配置

TVCMall MCP 的规范 endpoint 是 `https://openapi.tvc-mall.com/mcp`，其中 `/mcp` 是 endpoint 的组成部分，不要删除或重复追加。

1. 在 Codex 中调用 `$query-tvcmall-customer-data`，或直接提出 TVCMall 查询问题。
2. Skill 检查当前会话是否已提供 `tvcmall` MCP 及预期工具。
3. 如未安装，Skill 按 [TVCMall MCP](https://github.com/tvcmall-dev/mcp) 的连接方式注册远程 MCP，无需运行本地 Server。
4. 如没有个人 `TVCMALL_API_KEY`，请前往 https://www.tvcmall.com/user/agentkeys 登录并申请。
5. 用户明确确认明文存储后，本地脚本通过关闭输入回显的终端提示读取 Key，并更新用户级 Codex `config.toml`。
6. 重启 Codex 或开启新会话，再检查 `tvcmall` 工具并调用 `tvcmall_auth_status`。

生成的配置如下；`<TVCMALL_PAT>` 仅为占位符：

```toml
[mcp_servers.tvcmall]
url = "https://openapi.tvc-mall.com/mcp"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

Key 会按当前设计明文保存在用户级 Codex 配置中。Windows 默认路径为 `%USERPROFILE%\.codex\config.toml`，macOS 和 Linux 默认路径为 `~/.codex/config.toml`；设置 `CODEX_HOME` 时使用该目录下的 `config.toml`。

## 完整能力清单

所有业务能力均为只读。详细参数、默认值和 WebApi 映射见 [工具参数参考](.agents/skills/query-tvcmall-customer-data/references/tool-reference.md)。

| 类别 | 工具 | 对外参数 | 能力 |
| --- | --- | --- | --- |
| 认证 | `tvcmall_auth_status` | 无 | 检查当前 MCP 会话是否已加载 Key，不验证 Key 是否有效 |
| 商品 | `tvcmall_search_products` | `query`、`page`、`page_size` | 按 SKU 或关键词分页搜索商品 |
| 商品 | `tvcmall_get_product_detail` | `product_id` | 查询单个商品详情；ID 必须来自搜索结果 |
| 运费 | `tvcmall_estimate_shipping` | `sku`、`quantity`、`countrycode` | 估算未下单商品运费 |
| 订单 | `tvcmall_list_orders` | `start_date`、`end_date`、`status`、`page`、`page_size` | 分页查询订单列表 |
| 订单 | `tvcmall_get_order_detail` | `order_id` | 查询订单商品、金额和脱敏收货信息 |
| 物流 | `tvcmall_get_tracking_info` | `order_id` | 查询单个订单物流轨迹和订单运费 |
| 物流 | `tvcmall_batch_get_tracking` | `order_ids` | 批量查询 1 至 50 个订单的物流 |
| 积分 | `tvcmall_get_points` | 无 | 查询积分汇总 |
| 积分 | `tvcmall_list_point_records` | `direction`、`page`、`page_size` | 分页查询积分流水 |
| 余额 | `tvcmall_list_balance_records` | `direction`、`page`、`page_size` | 分页查询余额流水 |

不支持下单、付款、取消订单、修改地址、兑换积分或导出文件。

## 使用示例

```text
使用 $query-tvcmall-customer-data 列出我的 10 个订单。
搜索 SKU 为 100001234A 的商品并显示详情。
估算 2 件该商品寄往美国的运费。
显示我最近已发货订单的物流状态。
显示我的积分汇总和最近积分流水。
显示我最近的余额支出记录。
```

## 安全

- 不要将真实 `TVCMALL_API_KEY` 提交到 Git，也不要放入聊天、命令参数、日志或截图。
- `TVCMALL_API_KEY` 必须使用完整个人 PAT，不要添加 `Bearer ` 前缀。
- MCP 入站连接不要配置 `Authorization` header。
- 每位用户必须使用自己的 Key，不要使用网站密码、登录 token、OAuth token 或共享凭据。
- 不要尝试恢复服务端已脱敏的客户信息。
- endpoint 必须完整使用 `https://openapi.tvc-mall.com/mcp`；不要回退到 HTTP、删除 `/mcp` 或追加第二个 `/mcp`。

## 验证

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
python -m unittest discover -s tests -v
python -m py_compile .agents\skills\query-tvcmall-customer-data\scripts\configure_tvcmall_mcp.py
rg -n -F 'https://openapi.tvc-mall.com/mcp' README.md .agents\skills\query-tvcmall-customer-data
git diff --check
```

## 贡献

修改或新增 Skill 时：

1. 遵循标准 `SKILL.md`、`agents/openai.yaml`、`scripts/` 和 `references/` 结构；
2. 为脚本和 Skill 契约新增或更新测试；
3. 同步更新本 README 的 Skills 和能力清单；
4. 禁止提交真实凭据和客户数据；
5. 提交前运行完整验证。

## 相关链接

- [TVCMall MCP](https://github.com/tvcmall-dev/mcp)
- [申请 TVCMALL_API_KEY](https://www.tvcmall.com/user/agentkeys)
- [OpenAI Skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI MCP](https://learn.chatgpt.com/docs/extend/mcp)
