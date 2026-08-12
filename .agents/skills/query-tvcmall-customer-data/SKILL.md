---
name: query-tvcmall-customer-data
description: Configure and use the TVCMall Customer MCP for read-only product, shipping, order, tracking, points, and balance queries. Use when Codex needs to install or repair the tvcmall MCP connection, configure TVCMALL_API_KEY, or answer TVCMall customer-data questions.
---

# Query TVCMall Customer Data

## Prepare the MCP

1. Check for an MCP dependency identified as `tvcmall` and its expected tools.
2. If installation or repair is required, read [references/mcp-setup.md](references/mcp-setup.md) completely and follow it.
3. Run [scripts/configure_tvcmall_mcp.py](scripts/configure_tvcmall_mcp.py) only after the user confirms plaintext storage.
4. After configuration, ask the user to restart Codex or start a new session before calling business tools.

## Route Requests

Read [references/tool-routing.md](references/tool-routing.md) completely before selecting a tool. Ask only for parameters required by the selected tool, use bounded queries, and stop when the user's request is satisfied.

## Protect Customer Data

- Keep every operation read-only.
- Do not ask the user to provide a Key in chat, and do not print a Key from configuration, logs, errors, or tool output.
- Do not call the TVCMall WebApi directly or bypass MCP authorization.
- Give the direct answer first, followed by the minimum useful structured detail.
