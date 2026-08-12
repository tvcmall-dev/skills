# TVCMall 工具路由

## 全局规则

- 业务数据只能来自 `tvcmall` MCP 工具。
- 所有操作保持只读，只查询用户明确要求的范围。
- 不恢复已脱敏 PII，不暴露原始上游响应，也不输出认证数据。
- 使用有界分页；批量物流每次最多传入当前结果中的 50 个订单号。
- 列表查询默认 `page=1`、`page_size=20`。用户指定数量时，将 `page_size` 设置为该数量且不超过 50；例如“10 个订单”使用 `page=1`、`page_size=10`。
- `tvcmall_list_orders` 没有排序参数。按第一页返回顺序展示；工具 schema 或响应未证明排序语义时，不要声称结果严格按时间排序，并向用户说明边界。

## 路由表

| 用户意图 | 工具 | 必须遵循 |
| --- | --- | --- |
| 按 SKU 或关键词搜索商品 | `tvcmall_search_products` | 无结果时停止；有多个结果时要求用户确认，不自动选择 |
| 查看单个商品详情 | `tvcmall_get_product_detail` | 只使用搜索结果返回的 `product_id` |
| 估算未下单商品运费 | `tvcmall_estimate_shipping` | 要求提供 SKU、数量和两位国家代码 |
| 查询或筛选订单 | `tvcmall_list_orders` | 使用支持的状态、日期参数和有界分页 |
| 查看单个订单详情 | `tvcmall_get_order_detail` | 使用用户提供或工具返回的 `order_id` |
| 查看已下单商品的物流或订单运费 | `tvcmall_get_tracking_info` | 不要替换为商品运费估算 |
| 查看当前结果中多个订单的物流 | `tvcmall_batch_get_tracking` | 每次最多传 50 个订单号 |
| 查看积分汇总 | `tvcmall_get_points` | 不要与积分流水混淆 |
| 查看积分流水 | `tvcmall_list_point_records` | `direction` 使用 `all`、`got` 或 `used` |
| 查看余额流水 | `tvcmall_list_balance_records` | `direction` 使用 `all`、`income` 或 `expense` |

## 订单与物流

- 使用 `tvcmall_list_orders` 和支持的状态进行有界分页；未指定状态时使用 `V3All`。
- 使用 `tvcmall_get_order_detail` 查看已知订单。
- 使用 `tvcmall_get_tracking_info` 查询单个订单的物流或订单运费。如果缺少 `order_id`，先询问订单号；用户想从账户中选择时，先列出有限数量的订单并要求确认。
- 使用 `tvcmall_batch_get_tracking` 查询当前页订单的物流，每次不超过 50 个。
- 查询最近已发货订单的物流时，先调用 `tvcmall_list_orders(status=V3Shipped)`，再调用 `tvcmall_batch_get_tracking`。
- 状态映射：全部=`V3All`、待付款=`V3Unpaid`、待确认=`V3AwaitingConfirmation`、备货中=`V3Preparing`、已发货=`V3Shipped`、已完成=`V3Done`。

## 积分与余额

- `tvcmall_get_points`：积分汇总。
- `tvcmall_list_point_records`：积分流水。`direction` 使用 `all`、`got` 或 `used`；省略时使用 `all`。
- `tvcmall_list_balance_records`：余额流水。`direction` 使用 `all`、`income` 或 `expense`；省略时使用 `all`。

## 稳定错误

- `AUTH_REQUIRED`：引导用户配置或更换 Key；不要要求在聊天中提供 Key。
- `PERMISSION_DENIED`：说明可能缺少 scope 或 route allowlist；不要尝试绕过。
- `RATE_LIMITED`：建议等待后重试。
- `API_UNAVAILABLE`：说明 MCP 或 WebApi 暂时不可用；不要编造结果。
- `SESSION_NOT_FOUND`：要求用户重新连接或重启 Codex。
