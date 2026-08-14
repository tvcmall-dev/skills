---
name: query-tvcmall-customer-data
description: Use when Codex needs to install or repair the tvcmall MCP connection, configure TVCMALL_API_KEY, or query read-only TVCMall customer data such as products, shipping estimates, orders, tracking, points, and balance.
---

# Query TVCMall Customer Data

## Prepare the MCP

1. Check whether the current session has an MCP dependency named `tvcmall` and the expected tools.
2. If installation or repair is required, read [references/mcp-setup.md](references/mcp-setup.md) completely and follow it.
3. Run [scripts/configure_tvcmall_mcp.py](scripts/configure_tvcmall_mcp.py) only after the user confirms plaintext storage.
4. After configuration, ask the user to restart Codex or start a new session before calling business tools.

## Route Requests

Read [references/tool-routing.md](references/tool-routing.md) completely before selecting a tool. Inspect the current MCP tool schema before every tool call and obtain its required inputs, types, allowed values, defaults, and limits at runtime. Do not use static documentation as the tool parameter contract. Ask only for inputs required by the current schema, keep queries bounded to the user's request, and stop when the request is satisfied.

## Protect Customer Data

- Keep every operation read-only.
- Do not ask the user to provide a Key in chat, and do not print a Key from configuration, logs, errors, or tool output.
- Do not call the TVCMall WebApi directly or bypass MCP authorization.
- Give the direct answer first, followed by the minimum useful structured detail.
