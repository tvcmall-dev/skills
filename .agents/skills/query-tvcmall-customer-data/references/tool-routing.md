# TVCMall 工具路由

## 全局规则

- 只使用 `tvcmall` MCP 工具作为业务数据源。
- 所有操作保持只读，只查询用户明确要求的范围。
- 不恢复已脱敏 PII，不暴露上游原始正文，不输出认证数据。
- 使用有限分页；批量物流每次最多传入 50 个当前结果中的订单号。
- 列表查询默认使用 `page=1`、`page_size=20`。用户给出具体数量时，将 `page_size` 设为该数量且不超过 50；例如“最近 10 个订单”使用 `page=1`、`page_size=10`。
- `tvcmall_list_orders` 没有排序参数。按第一页响应顺序呈现结果；如果工具 schema 或响应不能证明排序语义，不要声称结果已严格按时间排序，并向用户说明这一限制。

## 路由表

| 用户意图 | 工具 | 必须遵守的行为 |
| --- | --- | --- |
| 按 SKU 或关键词搜索商品 | `tvcmall_search_products` | 无结果时停止；多结果时请用户选择，不擅自选中 |
| 查看单个商品详情 | `tvcmall_get_product_detail` | 只使用搜索结果返回的 `product_id` |
| 估算未下单商品运费 | `tvcmall_estimate_shipping` | 要求 SKU、数量和两位国家代码 |
| 查询或筛选订单 | `tvcmall_list_orders` | 使用受支持的状态和有限分页 |
| 查看单个订单详情 | `tvcmall_get_order_detail` | 使用用户提供或工具返回的 `order_id` |
| 查看单个已下单订单的物流或运费 | `tvcmall_get_tracking_info` | 不得改用商品运费估算 |
| 查看当前结果中多个订单的物流 | `tvcmall_batch_get_tracking` | 最多传入 50 个当前结果中的订单号 |
| 查看积分汇总 | `tvcmall_get_points` | 不要与积分流水混淆 |
| 查看积分流水 | `tvcmall_list_point_records` | `direction` 使用 `all`、`got` 或 `used` |
| 查看余额流水 | `tvcmall_list_balance_records` | `direction` 使用 `all`、`income` 或 `expense` |

## 订单与物流

- 使用 `tvcmall_list_orders` 按受支持状态和有限页数查询订单；未指定状态时使用 `V3All`。
- 使用 `tvcmall_get_order_detail` 查看已知订单。
- 使用 `tvcmall_get_tracking_info` 查询单个订单物流或已下单运费。缺少 `order_id` 时先询问订单号；如果用户要求从账户中选择，先列出有限数量的订单，再让用户确认。
- 使用 `tvcmall_batch_get_tracking` 查询当前页订单的物流，每次最多 50 个。
- 查询最近已发货订单的物流时，先调用 `tvcmall_list_orders(status=V3Shipped)`，再调用 `tvcmall_batch_get_tracking`。
- 订单状态映射：全部=`V3All`、未付款=`V3Unpaid`、待确认=`V3AwaitingConfirmation`、备货中=`V3Preparing`、已发货=`V3Shipped`、已完成=`V3Done`。

## 积分与余额

- `tvcmall_get_points`：积分汇总。
- `tvcmall_list_point_records`：积分流水，方向使用 `all`、`got` 或 `used`；省略 `direction` 时使用 `all`。
- `tvcmall_list_balance_records`：余额流水，方向使用 `all`、`income` 或 `expense`；省略 `direction` 时使用 `all`。

## 稳定错误

- `AUTH_REQUIRED`：引导配置或替换 Key，不要求在聊天中提供 Key。
- `PERMISSION_DENIED`：说明可能缺少 scope 或 route allowlist，不尝试绕过。
- `RATE_LIMITED`：建议等待后重试。
- `API_UNAVAILABLE`：说明 MCP 或 WebApi 暂时不可用，不编造结果。
- `SESSION_NOT_FOUND`：提示重新连接或重启 Codex。
