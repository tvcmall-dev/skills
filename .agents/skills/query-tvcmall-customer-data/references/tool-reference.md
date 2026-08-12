# TVCMall 工具与参数参考

本清单以当前 MCP Server 的 Zod input schema 和 HTTP client 为对外契约，并用 TVCMall WebApi 项目中的 Controller、action 和 DTO 核对参数映射。只向用户收集“对外参数”；固定参数和请求上下文由 MCP/WebApi 补全，不要要求用户提供。

## 参数通则

- `page` 从 1 开始，默认 1。
- `page_size` 默认 20，范围 1 至 50。
- 表中“固定或上下文参数”不是 MCP 对外参数。
- WebApi 会根据认证用户、语言、货币、国家和设备补全内部上下文；不要在对话中伪造这些值。

## 认证

### `tvcmall_auth_status`

- 对外参数：无。
- 行为：只检查当前 MCP 会话是否加载 `TVCMALL_API_KEY`，不验证 Key 有效性，不调用 WebApi。

## 商品与运费

### `tvcmall_search_products`

- 对外参数：`query` 为必填非空字符串；`page` 默认 1；`page_size` 默认 20、最大 50。
- WebApi：GET `/v3/product/list/search/mapping`。
- 参数映射：`query` -> body.`keywords`，`page` -> body.`pageindex`，`page_size` -> body.`pagesize`。
- 固定参数：body.`sort=default`、`attributes=[]`、`catalogCodes=[]`、`purchaseTag=0`、`url=/search`、`noAttr=true`、`fromAlgolia=true`。
- WebApi 依据：`ProductListController.SearchMapping` 和 `ProductListFilterConditionInputDto`。

### `tvcmall_get_product_detail`

- 对外参数：`product_id` 必填，格式必须是搜索结果返回的 `/details/...` 路径；不能传 SKU、关键词或内部商品 ID。
- WebApi：GET `/v3/productdetail/detail`。
- 参数映射：`product_id` -> body.`url`。
- WebApi 依据：`V3ProductController.Detail` 和 `ProductDetailInputDto.url`；`priceStep` 由 WebApi 根据用户上下文设置。

### `tvcmall_estimate_shipping`

- 对外参数：`sku` 为必填非空字符串；`quantity` 为 1 至 1000 的整数；`countrycode` 为两位国家代码并转为大写。
- WebApi：GET `/v3/productdetail/shipping/compute`。
- 参数映射：`sku` -> body.`sku`，`quantity` -> body.`quantity`，`countrycode` -> body.`countryCode`。
- WebApi 依据：`V3ProductController.ComputeShippingCosts` 和 `ComputeShippingCostsInputDto`。

## 订单与物流

### `tvcmall_list_orders`

- 对外参数：`start_date`、`end_date` 可选；`status` 默认 `V3All`；`page` 默认 1；`page_size` 默认 20、最大 50。
- 状态值：`V3All`、`V3Unpaid`、`V3AwaitingConfirmation`、`V3Preparing`、`V3Shipped`、`V3Done`。
- WebApi：POST `/v3/user/getorders`。
- 参数映射：`start_date` -> body.`BeginDate`，`end_date` -> body.`EndDate`，`status` -> body.`status`，`page` -> body.`pageindex`，`page_size` -> body.`pagesize`。
- 固定参数：body.`keywords=""`、body.`WithDetail=true`。
- WebApi 依据：`V3UserController.GetOrders` 和 `GetOrdersDto`。

### `tvcmall_get_order_detail`

- 对外参数：`order_id` 为必填非空字符串。
- WebApi：POST `/v3/order/detail`。
- 参数映射：`order_id` -> query.`orderId`。
- 默认参数：Controller 使用 `active=true`、`keyWords=null`、`pageIndex=1`、`pageSize=10`。
- WebApi 依据：`V3OrderController.OrderDetail`；Controller 在返回前校验订单归属。

### `tvcmall_get_tracking_info`

- 对外参数：`order_id` 为必填非空字符串。
- WebApi：GET `/order/getlogisticstracking`。
- 参数映射：`order_id` -> query.`orderId`。
- WebApi 依据：`OrderController.GetLogisticsTracking`；MCP PAT 场景会先校验订单归属。

### `tvcmall_batch_get_tracking`

- 对外参数：`order_ids` 为 1 至 50 个非空订单号组成的数组。
- WebApi：没有独立批量 route；MCP 对每个订单调用 `/order/getlogisticstracking` 并合并结果。
- 参数映射：数组中的每个值依次映射为 query.`orderId`。

## 积分与余额

### `tvcmall_get_points`

- 对外参数：无。
- WebApi：GET `/v3/user/points/stat`。
- 固定参数：不传 `type`，使用 `V3UserController.GetUserAccountInfo` 的默认值 `type=points`。

### `tvcmall_list_point_records`

- 对外参数：`direction` 可取 `all`、`got`、`used`，默认 `all`；`page` 默认 1；`page_size` 默认 20、最大 50。
- WebApi：GET `/v3/user/points/list`。
- 参数映射：`page` -> query.`pageindex`，`page_size` -> query.`pagesize`；`all` -> `pointstype=0`，`got` -> `pointstype=1`，`used` -> `pointstype=2`。
- WebApi 依据：`V3UserController.GetAccumulatePointsList`；`pointstype` 中 1 表示获得、2 表示消费，默认 0 表示全部。

### `tvcmall_list_balance_records`

- 对外参数：`direction` 可取 `all`、`income`、`expense`，默认 `all`；`page` 默认 1；`page_size` 默认 20、最大 50。
- WebApi：GET `/v3/user/balance/list`。
- 参数映射：`page` -> query.`pageindex`，`page_size` -> query.`pagesize`；`all` -> `pointstype=0`，`income` -> `pointstype=1`，`expense` -> `pointstype=2`。
- WebApi 依据：`V3UserController.GetBalanceList`；语言和币种由 WebApi 请求上下文补全。
