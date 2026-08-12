# TVCMall Tool Routing

## Global Rules

- Use only `tvcmall` MCP tools as the business-data source.
- Keep every operation read-only and query only the scope explicitly requested by the user.
- Do not recover masked PII, expose raw upstream response bodies, or output authentication data.
- Use bounded pagination. For batch tracking, pass no more than 50 order numbers from the current result set per call.
- List queries default to `page=1` and `page_size=20`. When the user specifies a count, set `page_size` to that count, up to 50; for example, use `page=1` and `page_size=10` for "10 orders."
- `tvcmall_list_orders` has no sorting parameter. Present results in the order returned on the first page; when the tool schema or response does not prove sorting semantics, do not claim that results are strictly sorted by time.
- Product and shipping tools can be attempted with the default `tmcp_catalog.read` header without asking the user to apply for a personal Key first.
- Account tools require a personal Key: orders, tracking, points, and balance must not be attempted with only `tmcp_catalog.read`.

## Routing Table

| User Intent | Tool | Required Behavior |
| --- | --- | --- |
| Search for a product by SKU or keyword | `tvcmall_search_products` | Stop when there are no results; when there are multiple results, ask the user to choose instead of selecting one automatically |
| View one product's details | `tvcmall_get_product_detail` | Use only the `product_id` returned by search results |
| Estimate shipping for products not yet ordered | `tvcmall_estimate_shipping` | Require the SKU, quantity, and two-letter country code |
| Query or filter orders | `tvcmall_list_orders` | Use supported status, date parameters, and bounded pagination |
| View one order's details | `tvcmall_get_order_detail` | Use an `order_id` supplied by the user or returned by a tool |
| View tracking or shipping cost for one placed order | `tvcmall_get_tracking_info` | Do not substitute a product shipping estimate |
| View tracking for multiple orders in the current result set | `tvcmall_batch_get_tracking` | Pass no more than 50 order numbers per call |
| View a points summary | `tvcmall_get_points` | Do not confuse it with points records |
| View points records | `tvcmall_list_point_records` | Use `all`, `got`, or `used` for `direction` |
| View balance records | `tvcmall_list_balance_records` | Use `all`, `income`, or `expense` for `direction` |

## Orders and Tracking

- Use `tvcmall_list_orders` with supported status, date parameters, and bounded pages to query orders. Use `V3All` when no status is specified.
- Use `tvcmall_get_order_detail` to view a known order.
- Use `tvcmall_get_tracking_info` to query tracking or shipping cost for a single placed order. If `order_id` is missing, ask for the order number first. If the user wants to select one from the account, list a bounded number of orders and ask the user to confirm.
- Use `tvcmall_batch_get_tracking` to query tracking for orders on the current page, with no more than 50 per call.
- To query tracking for recently shipped orders, call `tvcmall_list_orders(status=V3Shipped)` first and then call `tvcmall_batch_get_tracking`.
- Order status mapping: all=`V3All`, unpaid=`V3Unpaid`, awaiting confirmation=`V3AwaitingConfirmation`, preparing=`V3Preparing`, shipped=`V3Shipped`, done=`V3Done`.

## Points and Balance

- `tvcmall_get_points`: points summary.
- `tvcmall_list_point_records`: points records. Use `all`, `got`, or `used` for `direction`. When `direction` is omitted, use `all`.
- `tvcmall_list_balance_records`: balance records. Use `all`, `income`, or `expense` for `direction`. When `direction` is omitted, use `all`.

## Stable Errors

- If a product or shipping tool returns `AUTH_REQUIRED` or `401`, explain that default `catalog.read` access was rejected and guide the user to apply for a personal Key; do not ask for the Key in chat.
- `AUTH_REQUIRED` for account tools: guide the user through configuring or replacing the personal Key; do not ask for the Key in chat.
- `PERMISSION_DENIED`: explain that a scope or route allowlist may be missing; do not try to bypass it.
- `RATE_LIMITED`: suggest waiting before retrying.
- `API_UNAVAILABLE`: explain that the MCP or WebApi is temporarily unavailable; do not fabricate results.
- `SESSION_NOT_FOUND`: ask the user to reconnect or restart Codex.
