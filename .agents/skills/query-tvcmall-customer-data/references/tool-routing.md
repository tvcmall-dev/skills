# TVCMall Tool Routing

## Global Rules

- Use only `tvcmall` MCP tools as the business-data source.
- Business route mappings describe MCP behavior only. Do not call the WebApi route directly or bypass MCP authorization.
- Inspect the current MCP tool schema before each call. Treat that schema as the source of truth for inputs, types, allowed values, defaults, and limits.
- Keep every operation read-only and query only the scope explicitly requested by the user.
- Do not recover masked PII, expose raw upstream response bodies, or output authentication data.
- Keep pagination and batch operations bounded by both the user's request and the limits in the current MCP tool schema.
- When the current MCP tool schema or response does not prove sorting semantics, do not claim that results are strictly sorted by time, price, or another field.
- Product and shipping tools can be attempted with the default `tmcp_catalog.read` header without asking the user to apply for a personal Key first.
- Account tools require a personal Key: orders, tracking, points, and balance must not be attempted with only `tmcp_catalog.read`.

## Routing Table

| User Intent | Tool | Required Behavior |
| --- | --- | --- |
| Search for a product by SKU or keyword | `tvcmall_search_products` | Stop when there are no results; when there are multiple results, present choices instead of selecting one automatically |
| View one product's details | `tvcmall_get_product_detail` | Use the product reference returned by search in the field required by the current schema |
| Estimate shipping for products not yet ordered | `tvcmall_estimate_shipping` | Collect only the destination and product inputs required by the current schema |
| Query or filter orders | `tvcmall_list_orders` | Use only filters and pagination options exposed by the current schema |
| View one order's details | `tvcmall_get_order_detail` | Use an order reference supplied by the user or returned by a tool |
| View tracking or shipping cost for one placed order | `tvcmall_get_tracking_info` | Do not substitute a product shipping estimate |
| View tracking for multiple orders in the current result set | `tvcmall_batch_get_tracking` | Respect the collection and size limits in the current schema |
| View a points summary | `tvcmall_get_points` | Do not confuse it with points records |
| View points records | `tvcmall_list_point_records` | Use only filters exposed by the current schema |
| View the current balance summary | `tvcmall_get_balance` | Use the MCP tool backed by `GET api/v3/user/points/stat?type=balance`; do not confuse it with balance records |
| View balance records | `tvcmall_list_balance_records` | Use only filters exposed by the current schema |

## Orders and Tracking

- Use `tvcmall_list_orders` with the current schema's supported filters and bounded pagination.
- Use `tvcmall_get_order_detail` to view a known order.
- Use `tvcmall_get_tracking_info` to query tracking or shipping cost for a single placed order. If the current schema's required order reference is unavailable, ask the user for it. If the user wants to select an order from the account, list a bounded set and ask the user to confirm.
- Use `tvcmall_batch_get_tracking` for multiple orders only when requested, and stay within the current schema's collection limits.
- To query tracking for recently shipped orders, first use the order-list filter that the current schema defines for shipped orders, then call the batch tracking tool with the returned order references.

## Points and Balance

- Use `tvcmall_get_points` for a points summary.
- Use `tvcmall_list_point_records` for points records and apply only filter values exposed by the current schema.
- Use `tvcmall_get_balance` for the current available and frozen balance summary. The MCP tool is backed by `GET api/v3/user/points/stat?type=balance`; never call that WebApi route directly.
- Use `tvcmall_list_balance_records` for balance records and apply only filter values exposed by the current schema.

## Stable Errors

- If a product or shipping tool returns `AUTH_REQUIRED` or `401`, explain that default `catalog.read` access was rejected and guide the user to apply for a personal Key; do not ask for the Key in chat.
- `AUTH_REQUIRED` for account tools: guide the user through configuring or replacing the personal Key; do not ask for the Key in chat.
- `PERMISSION_DENIED`: explain that a scope or route allowlist may be missing; do not try to bypass it.
- `RATE_LIMITED`: suggest waiting before retrying.
- `API_UNAVAILABLE`: explain that the MCP or WebApi is temporarily unavailable; do not fabricate results.
- `SESSION_NOT_FOUND`: ask the user to reconnect or restart Codex.
