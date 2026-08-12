# TVCMall Customer Skill 设计

## 目标

初始化 `tvcmall-dev/skills` 独立仓库，并交付首个基于 TVCMall Customer MCP 的标准 Codex Skill：`query-tvcmall-customer-data`。

该 Skill 为 TVCMall 用户提供商品、未下单商品运费、订单、物流、积分和余额流水的只读查询。它在首次使用时检查 TVCMall MCP 是否已经注册；未注册或缺少 `TVCMALL_API_KEY` 时，通过对话引导用户完成配置。仓库结构允许后续增加其他 TVCMall Skills。

## 非目标

- 不在本仓库中实现、复制或运行 TVCMall MCP Server。
- 不修改 MCP Server 的认证、session、scope、route allowlist 或数据脱敏逻辑。
- 不支持下单、支付、取消订单、修改地址、积分兑换或文件导出。
- 不把真实 MCP Key、客户数据或本机用户配置提交到 Git。
- 首版不为 Claude Code、Cursor 或其他 MCP Client 自动配置连接，只支持 Codex。

## 仓库结构

仓库采用 OpenAI 官方 Codex Skill 结构：

```text
skills/
  .agents/
    skills/
      query-tvcmall-customer-data/
        SKILL.md
        agents/
          openai.yaml
        scripts/
          configure_tvcmall_mcp.py
        references/
          mcp-setup.md
          tool-routing.md
  docs/
    superpowers/
      specs/
      plans/
  tests/
    test_configure_tvcmall_mcp.py
  AGENTS.md
  README.md
```

`SKILL.md` 是触发条件、工作流和安全边界的唯一主入口。`agents/openai.yaml` 提供 UI 元数据、调用提示和名为 `tvcmall` 的 Streamable HTTP MCP 依赖声明。`scripts/` 只承担需要确定性行为的 Codex 配置检查与更新；`references/` 保存详细安装说明和 tool 路由表，按需加载，避免主 Skill 过长。

根目录 `README.md` 是仓库的标准用户入口，至少包含：项目定位、可用 Skill 列表、支持的查询能力、安装或仓库级发现方式、首次 MCP 配置流程、`TVCMALL_API_KEY` 申请入口、使用示例、安全警告、验证命令和贡献说明。README 中只使用 Key 占位符，不包含真实凭据，并将 `https://mcpserver.tvc-mall.com` 作为 TVCMall MCP 的标准 HTTPS 地址。

## Skill 触发与职责

Skill 名称为 `query-tvcmall-customer-data`。以下意图触发该 Skill：

- 搜索商品或查询商品详情；
- 估算尚未下单商品的运费；
- 查询订单列表、订单详情、已下单运费或物流；
- 查询积分汇总、积分流水或余额流水；
- 安装、连接、检查或修复 TVCMall MCP；
- 配置或更新 `TVCMALL_API_KEY`。

Skill 负责 MCP 准备检查、缺失参数追问、tool 选择、跨 tool 编排、稳定错误解释和结果呈现。MCP Server 继续负责认证上下文、API schema、WebApi 调用、业务授权、错误映射和数据脱敏。

## 首次使用与配置流程

### 1. 检查 MCP

在执行 TVCMall 业务查询前，Skill 先检查当前会话是否存在标识为 `tvcmall` 的 MCP 连接和预期 tools。存在时调用 `tvcmall_auth_status`；不存在时进入安装流程。

这里的“安装 MCP Server”是参考 `https://github.com/tvcmall-dev/mcp` 的接入方式，将远程 Streamable HTTP endpoint 注册到 Codex 用户级配置中，不克隆、不构建、不启动服务端仓库。首版固定使用用户指定的标准地址 `https://mcpserver.tvc-mall.com`，不得回退到旧的临时 HTTP 地址，也不得擅自追加 `/mcp` 或其他路径。

### 2. 处理 Key

Skill 通过对话询问用户是否已有 `TVCMALL_API_KEY`：

- 如果没有，提供 `https://www.tvcmall.com/user/agentkeys`，说明需先登录并申请个人 Key；停止配置，等待用户取得 Key 后继续。
- 如果已有，说明 Key 将按用户选择明文保存在 Codex 用户级 `config.toml`，然后启动本机配置脚本。

真实 Key 不要求用户粘贴到聊天中。脚本通过终端无回显输入读取 Key，不接受命令行 Key 参数，不打印 Key，也不把 Key写入 shell 历史。脚本只接受符合 `tmcp_v1_{tokenId}.{secret}` 基本格式、无首尾空白的完整值；`TVCMALL_API_KEY` 不添加 `Bearer ` 前缀。

### 3. 更新 Codex 配置

脚本定位 Codex 用户级配置：默认使用 `CODEX_HOME/config.toml`，未设置 `CODEX_HOME` 时使用用户目录下 `.codex/config.toml`。测试可通过显式的测试配置路径覆盖，不能触碰真实用户配置。

写入目标为：

```toml
[mcp_servers.tvcmall]
url = "https://mcpserver.tvc-mall.com"
http_headers = { "TVCMALL_API_KEY" = "<用户输入的完整 Key>" }
```

更新必须满足：

1. 写入前为现有 `config.toml` 创建同目录备份。
2. 解析并验证现有 TOML；只新增或替换 `[mcp_servers.tvcmall]` 及其子表，保留其他顶层配置和 MCP Server。无效 TOML 不得覆盖。
3. 采用临时文件加原子替换，避免中途失败损坏配置。
4. Key 中的 TOML 特殊字符必须正确转义。
5. 成功输出只报告配置路径、MCP 名称和是否创建备份，不显示 Key。
6. 重复运行保持幂等，不产生重复的 `tvcmall` section。

### 4. 重启与验证

由于 Codex 需要重新加载 MCP 配置，配置完成后 Skill 提示用户重启 Codex 或新建会话。重新连接后先检查 `tvcmall` tools，再调用 `tvcmall_auth_status`。

`configured: true` 只表示当前 MCP session 已载入 PAT，不代表 Key 已通过 WebApi 验证、未过期或拥有所需 scope。只有后续只读业务调用成功，才能确认相应权限可用。

## 查询 Tool 路由

| 用户意图 | MCP Tool | 约束 |
| --- | --- | --- |
| 按 SKU 或关键词查商品 | `tvcmall_search_products` | 多个结果时先让用户确认，不擅自选中 |
| 查看唯一商品详情 | `tvcmall_get_product_detail` | `product_id` 必须来自搜索结果 |
| 估算未下单商品运费 | `tvcmall_estimate_shipping` | 要求 SKU、数量和两位国家代码 |
| 查询订单 | `tvcmall_list_orders` | 使用受支持的状态和有限分页 |
| 查询订单详情 | `tvcmall_get_order_detail` | 使用用户提供或查询返回的 `order_id` |
| 查询单个订单物流或运费 | `tvcmall_get_tracking_info` | 已下单运费不得使用商品运费估算 |
| 查询多个订单物流 | `tvcmall_batch_get_tracking` | 只传当前结果中的订单号，最多 50 个 |
| 查询积分汇总 | `tvcmall_get_points` | 与积分流水、余额流水区分 |
| 查询积分流水 | `tvcmall_list_point_records` | `direction` 使用 `all`、`got` 或 `used` |
| 查询余额流水 | `tvcmall_list_balance_records` | `direction` 使用 `all`、`income` 或 `expense` |

组合查询允许有限编排。例如“最近已发货订单的物流”先调用 `tvcmall_list_orders(status=V3Shipped)`，再把当前结果中的订单号传给 `tvcmall_batch_get_tracking`。不得无限翻页、扩大用户查询范围或绕过 MCP 直接调用 TVCMall WebApi。

## 认证与安全边界

- 入站 MCP Header 固定为 `TVCMALL_API_KEY`，值为完整个人 PAT，不添加 `Bearer `。
- 不配置入站 `Authorization`，不接受网站密码、网站登录 token、OAuth token 或服务器共享 PAT。
- 真实 Key 按用户明确选择明文保存在用户级 Codex 配置中；配置前必须提示该风险和文件位置。
- 仓库文档、测试、fixtures 和示例只能使用显然无效的占位符或假 Key。
- Skill、脚本、日志、错误、tool 输出和最终回答不得回显完整 Key。
- MCP endpoint 固定为 `https://mcpserver.tvc-mall.com`。不得使用旧的公网 HTTP 地址，也不得因连接失败自动降低到 HTTP。
- 不恢复或推断 MCP/WebApi 已脱敏的 PII，不输出不必要的完整地址、电话或上游原始正文。

## 错误处理

- MCP 未注册：解释将按官方 README 注册远程连接，取得确认后运行配置流程。
- MCP endpoint 返回网络错误或 `5xx`：报告标准 HTTPS 服务当前不可用，保留配置并建议稍后重试；不得回退到旧 HTTP endpoint。
- Key 缺失：提供申请页面并等待用户完成，不生成或猜测 Key。
- Key 格式错误：拒绝写入，仅说明格式要求，不回显输入值。
- 配置解析或写入失败：保留原文件和备份，报告非敏感错误与恢复路径。
- `AUTH_REQUIRED`：提示 Key 缺失、格式错误、失效或被撤销，并提供重新配置入口。
- `PERMISSION_DENIED`：说明可能缺少 scope 或 route allowlist，不建议绕过。
- `RATE_LIMITED`：建议稍后重试。
- `API_UNAVAILABLE`：说明 MCP 或 WebApi 暂时不可用，不编造业务结果。
- `SESSION_NOT_FOUND`：提示重新连接或重启 Codex。

## 测试与验收

### 结构与元数据

- 使用官方 `skill-creator` 校验器验证 Skill 目录、frontmatter 和 `agents/openai.yaml`。
- 确认 Skill 位于 `.agents/skills/query-tvcmall-customer-data`，并声明 `tvcmall` MCP 依赖。
- 确认仓库没有真实 Key、真实客户数据或非占位 MCP 凭据。
- 检查根目录 `README.md` 覆盖安装、首次配置、Key 申请、查询示例、安全边界、测试与贡献入口，且其中的命令和路径与实际仓库结构一致。
- 检查所有安装示例精确使用 `https://mcpserver.tvc-mall.com`，且仓库不包含旧的临时 HTTP 地址。

### 配置脚本

- 在临时目录测试空配置、已有其他 MCP、已有 `tvcmall` 及其子表、CRLF/LF 和无尾换行文件。
- 验证更新前备份、原子写入、其他配置保留、重复运行幂等和 TOML 转义。
- 验证缺失 Key、格式错误、无写权限和无效 TOML 时安全失败。
- 捕获 stdout/stderr，断言 Key 及其 `Bearer` 形式均未出现。
- 测试绝不能读取或修改开发者真实的 Codex 用户配置。

### Skill 行为

- MCP 已连接且已配置时直接执行正确查询。
- MCP 缺失时进入安装流程，不尝试克隆或运行服务端仓库。
- MCP 安装配置精确写入 `https://mcpserver.tvc-mall.com`，不自动追加 `/mcp`。
- 用户没有 Key 时只引导到申请页面并等待。
- 商品多结果时先确认；唯一结果按需查详情。
- 已下单运费使用物流 tool，不使用商品运费估算。
- 最近已发货订单物流使用订单列表加批量物流。
- 积分汇总、积分流水和余额流水路由正确。
- 认证和上游错误使用稳定、安全的解释，不泄露凭据或 PII。

## 参考依据

- OpenAI Skills：`https://learn.chatgpt.com/docs/build-skills`
- OpenAI MCP：`https://learn.chatgpt.com/docs/extend/mcp`
- TVCMall MCP：`https://github.com/tvcmall-dev/mcp`
- TVCMall Agent Key：`https://www.tvcmall.com/user/agentkeys`
