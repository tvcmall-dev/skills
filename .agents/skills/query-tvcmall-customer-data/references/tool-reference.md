# TVCMall Tool and Parameter Reference

This list uses the current MCP Server Zod input schemas and HTTP client as the external contract, and validates parameter mappings against the TVCMall WebApi project's controllers, actions, and DTOs. Collect only external parameters from the user; fixed parameters and request context are filled by the MCP or WebApi.

## Parameter Rules

- `page` starts at 1 and defaults to 1.
- `page_size` defaults to 20 and accepts values from 1 to 50.
- Values listed as fixed or context parameters are not MCP external parameters.
- WebApi fills internal context such as authenticated user, language, currency, country, and device. Do not invent these values in conversation.

## Auth

### `tvcmall_auth_status`

- External parameters: none.
- Behavior: checks only whether the current MCP session loaded `TVCMALL_API_KEY`; it does not validate Key authorization and does not call WebApi.

## Products and Shipping

### `tvcmall_search_products`

- External parameters: `query` is a required non-empty string; `page` defaults to 1; `page_size` defaults to 20 and has a maximum of 50.
- WebApi: GET `/v3/product/list/search/mapping`.
- Mapping: `query` -> body.`keywords`, `page` -> body.`pageindex`, `page_size` -> body.`pagesize`.
- Fixed parameters: body.`sort=default`, `attributes=[]`, `catalogCodes=[]`, `purchaseTag=0`, `url=/search`, `noAttr=true`, `fromAlgolia=true`.
- WebApi evidence: `ProductListController.SearchMapping` and `ProductListFilterConditionInputDto`.

### `tvcmall_get_product_detail`

- External parameters: `product_id` is required and must be the `/details/...` path returned by search results; do not pass a SKU, keyword, or internal product ID.
- WebApi: GET `/v3/productdetail/detail`.
- Mapping: `product_id` -> body.`url`.
- WebApi evidence: `V3ProductController.Detail` and `ProductDetailInputDto.url`; `priceStep` is set by WebApi from user context.

### `tvcmall_estimate_shipping`

- External parameters: `sku` is a required non-empty string; `quantity` is an integer from 1 to 1000; `countrycode` is a two-letter country code and is normalized to uppercase.
- WebApi: GET `/v3/productdetail/shipping/compute`.
- Mapping: `sku` -> body.`sku`, `quantity` -> body.`quantity`, `countrycode` -> body.`countryCode`.
- WebApi evidence: `V3ProductController.ComputeShippingCosts` and `ComputeShippingCostsInputDto`.

## Orders and Tracking

### `tvcmall_list_orders`

- External parameters: optional `start_date` and `end_date`; `status` defaults to `V3All`; `page` defaults to 1; `page_size` defaults to 20 and has a maximum of 50.
- Status values: `V3All`, `V3Unpaid`, `V3AwaitingConfirmation`, `V3Preparing`, `V3Shipped`, `V3Done`.
- WebApi: POST `/v3/user/getorders`.
- Mapping: `start_date` -> body.`BeginDate`, `end_date` -> body.`EndDate`, `status` -> body.`status`, `page` -> body.`pageindex`, `page_size` -> body.`pagesize`.
- Fixed parameters: body.`keywords=""`, body.`WithDetail=true`.
- WebApi evidence: `V3UserController.GetOrders` and `GetOrdersDto`.

### `tvcmall_get_order_detail`

- External parameters: `order_id` is a required non-empty string.
- WebApi: POST `/v3/order/detail`.
- Mapping: `order_id` -> query.`orderId`.
- Default parameters: the controller uses `active=true`, `keyWords=null`, `pageIndex=1`, `pageSize=10`.
- WebApi evidence: `V3OrderController.OrderDetail`; the controller verifies order ownership before returning data.

### `tvcmall_get_tracking_info`

- External parameters: `order_id` is a required non-empty string.
- WebApi: GET `/order/getlogisticstracking`.
- Mapping: `order_id` -> query.`orderId`.
- WebApi evidence: `OrderController.GetLogisticsTracking`; the MCP PAT path verifies order ownership before returning data.

### `tvcmall_batch_get_tracking`

- External parameters: `order_ids` is an array of 1 to 50 non-empty order numbers.
- WebApi: no dedicated batch route; the MCP calls `/order/getlogisticstracking` for each order and merges the results.
- Mapping: each array value maps to query.`orderId` in sequence.

## Points and Balance

### `tvcmall_get_points`

- External parameters: none.
- WebApi: GET `/v3/user/points/stat`.
- Fixed parameters: no `type` is passed; this uses the `V3UserController.GetUserAccountInfo` default `type=points`.

### `tvcmall_list_point_records`

- External parameters: `direction` accepts `all`, `got`, or `used` and defaults to `all`; `page` defaults to 1; `page_size` defaults to 20 and has a maximum of 50.
- WebApi: GET `/v3/user/points/list`.
- Mapping: `page` -> query.`pageindex`, `page_size` -> query.`pagesize`; `all` -> `pointstype=0`, `got` -> `pointstype=1`, `used` -> `pointstype=2`.
- WebApi evidence: `V3UserController.GetAccumulatePointsList`; `pointstype` value 1 means gained, 2 means spent, and the default 0 means all.

### `tvcmall_list_balance_records`

- External parameters: `direction` accepts `all`, `income`, or `expense` and defaults to `all`; `page` defaults to 1; `page_size` defaults to 20 and has a maximum of 50.
- WebApi: GET `/v3/user/balance/list`.
- Mapping: `page` -> query.`pageindex`, `page_size` -> query.`pagesize`; `all` -> `pointstype=0`, `income` -> `pointstype=1`, `expense` -> `pointstype=2`.
- WebApi evidence: `V3UserController.GetBalanceList`; language and currency are filled by WebApi request context.
