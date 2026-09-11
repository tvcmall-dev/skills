# TVCMall Skills

This repository contains reusable TVCMall Agent Skills. The current Skill is `query-tvcmall-customer-data`, which provides authenticated, read-only TVCMall queries through the TVCMall Customer MCP and guides first-time `TVCMALL_API_KEY` configuration.

## Skills

| Skill | Capabilities |
| --- | --- |
| `query-tvcmall-customer-data` | Authenticated, read-only product search and filters, pre-order shipping estimates, orders, tracking, remaining points, current balance, and balance-record queries |

## Requirements

- An agent tool that supports Agent Skills and MCP, such as the Codex app / CLI, Claude Code / Claude Code CLI, Gemini CLI, GitHub Copilot CLI, Cursor CLI, or Qwen Code CLI;
- PowerShell 7.0 or later is preferred for the native Windows configuration dialog; the launcher selects a standard installation or the Codex bundled runtime, uses the Windows PowerShell 5.1 fallback when neither is found, and does not require Python on Windows;
- Python 3.11 or later for configuration on macOS/Linux, the optional cross-platform fallback on Windows, and repository validation;
- A personal `TVCMALL_API_KEY`.

## Install This Skill In Agent Tools

For manual installation, clone this repository first:

```powershell
git clone https://github.com/tvcmall-dev/skills.git
cd skills
```

The Skill folder to install is `.agents/skills/query-tvcmall-customer-data`. Use the folder as-is; it already contains `SKILL.md`, `agents/openai.yaml`, `scripts/`, and `references/`.

Codex uses different locations for project-scoped, manually managed user-scoped, and installer-managed Skills:

- For one repository, copy or keep the Skill at `$REPO_ROOT/.agents/skills/query-tvcmall-customer-data`. Codex scans `.agents/skills` from the current working directory up to the repository root.
- For a manual Codex user-level installation, copy the Skill to `$HOME/.agents/skills/query-tvcmall-customer-data`. In PowerShell, `$HOME` resolves to the current user's profile directory.
- For a Codex-managed user installation, ask `$skill-installer` to install `https://github.com/tvcmall-dev/skills/tree/main/.agents/skills/query-tvcmall-customer-data`; this method does not require a local clone. The installer places the Skill at `$CODEX_HOME/skills/query-tvcmall-customer-data`, which defaults to `$HOME/.codex/skills/query-tvcmall-customer-data` when `CODEX_HOME` is not set.

| Agent Tool | Project-Level Install | User-Level Install | Verify or Invoke |
| --- | --- | --- | --- |
| Codex app / CLI | Copy or keep the folder at `$REPO_ROOT/.agents/skills/query-tvcmall-customer-data` in the target repository | Use `$skill-installer`, or copy the folder to `$HOME/.agents/skills/query-tvcmall-customer-data` | Invoke `$query-tvcmall-customer-data`, or ask a matching TVCMall question |
| Claude Code / Claude Code CLI | Copy the folder to `.claude/skills/query-tvcmall-customer-data` in your project | Copy the folder to `$HOME/.claude/skills/query-tvcmall-customer-data` | Invoke `/query-tvcmall-customer-data`, or let Claude Code select it from the description |
| Gemini CLI | Run `gemini skills install https://github.com/tvcmall-dev/skills.git --path .agents/skills/query-tvcmall-customer-data --scope workspace --consent`, or `gemini skills link .agents/skills/query-tvcmall-customer-data --scope workspace` from this repository | Use the same `gemini skills install` command with `--scope user`, or copy the folder to `$HOME/.gemini/skills/query-tvcmall-customer-data` | Run `gemini skills list --all` or `/skills list`, then ask a matching TVCMall question |
| GitHub Copilot CLI | Keep the folder at `.agents/skills/query-tvcmall-customer-data`, copy it to `.github/skills/query-tvcmall-customer-data`, or run `copilot skill add .agents/skills/query-tvcmall-customer-data` | Copy the folder to `$HOME/.copilot/skills/query-tvcmall-customer-data` or `$HOME/.agents/skills/query-tvcmall-customer-data` | In a Copilot CLI session, run `/skills reload` and `/skills info query-tvcmall-customer-data` |
| Cursor CLI | Keep the folder at `.agents/skills/query-tvcmall-customer-data`, or copy it to `.cursor/skills/query-tvcmall-customer-data` | Copy the folder to `$HOME/.agents/skills/query-tvcmall-customer-data` or `$HOME/.cursor/skills/query-tvcmall-customer-data` | Invoke `/query-tvcmall-customer-data`, attach it with `@query-tvcmall-customer-data`, or ask a matching TVCMall question |
| Qwen Code CLI | Copy the folder to `.qwen/skills/query-tvcmall-customer-data` in your project | Copy the folder to `$HOME/.qwen/skills/query-tvcmall-customer-data` | Use `/skills` to inspect available Skills, or ask a matching TVCMall question |

The installed Skill is available on the next turn. If Codex does not detect it, restart Codex and try again.

Official references:

- [OpenAI Skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/)
- [GitHub Copilot CLI Skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Qwen Code Agent Skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/)

## First-Time Setup

The canonical TVCMall MCP endpoint is `https://openai.tvc-mall.com/mcp`. The `/mcp` path is part of the endpoint; do not remove it or append it a second time.

1. Invoke `$query-tvcmall-customer-data`, `/query-tvcmall-customer-data`, or ask a TVCMall query directly.
2. The Skill checks whether the current session provides the `tvcmall` MCP and expected tools.
3. If the MCP is not installed, the Skill follows the connection method documented by [TVCMall MCP](https://github.com/tvcmall-dev/mcp) and registers the remote MCP without running a local server.
4. If you do not have a personal `TVCMALL_API_KEY`, sign in and apply at https://www.tvcmall.com/user/agentkeys. Do not call any TVCMall business tool until the Key is configured.
5. After you explicitly confirm plaintext storage, the Skill resolves the installed launcher to an absolute path. On Windows, it runs `scripts/launch_tvcmall_mcp_windows.cmd`, which checks PowerShell 7.0 or later in the standard installation directory and the current user's Codex bundled-runtime location, then uses the Windows PowerShell 5.1 fallback when necessary. The launcher does not search the current project or arbitrary `PATH` entries. It opens `scripts/configure_tvcmall_mcp_windows.ps1` as a local masked dialog without Python and without hiding startup failures. On macOS/Linux, or as an optional Windows fallback when Python 3.11 or later is already available, the Skill runs `scripts/configure_tvcmall_mcp.py` in a visible operating-system terminal with input echo disabled. Enter the complete personal Key only in the masked dialog or at the fallback script's hidden prompt. The Skill must never ask for or receive the Key in chat or an Agent client's embedded PTY, and must not pass it through command-line arguments, environment variables, or piped input. If automatic launch fails, the Skill gives you the exact non-secret command with the resolved absolute launcher or script path to run manually in a system terminal.
6. Restart Codex or start a new session, then check the `tvcmall` tools and call `tvcmall_auth_status`.

The generated configuration looks like this. `<TVCMALL_PAT>` is a placeholder only:

```toml
[mcp_servers.tvcmall]
url = "https://openai.tvc-mall.com/mcp"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

The Key is stored in plaintext in the user-level Codex configuration by the current design. The default path is `%USERPROFILE%\.codex\config.toml` on Windows and `~/.codex/config.toml` on macOS and Linux. Both configuration scripts use `config.toml` under `CODEX_HOME` when that environment variable is set.

## Complete Capability List

All business capabilities are read-only. Tool parameters, defaults, allowed values, and limits are read dynamically from the current MCP tool schema at runtime.

| Category | Tool | Capability |
| --- | --- | --- |
| Auth | `tvcmall_auth_status` | Checks whether the current MCP session loaded a Key; it does not validate authorization |
| Products | `tvcmall_search_products` | Searches products by SKU, keyword, or publish-date range and reports the authoritative result total; requires a personal Key |
| Products | `tvcmall_get_product_filters` | Resolves dynamic product attribute filter Codes from a search result; requires a personal Key |
| Products | `tvcmall_get_product_detail` | Retrieves one product detail record using an identifier returned by product search; requires a personal Key |
| Shipping | `tvcmall_estimate_shipping` | Estimates pre-order shipping cost for a product; requires a personal Key |
| Orders | `tvcmall_list_orders` | Lists and filters orders; requires a personal Key |
| Orders | `tvcmall_get_order_detail` | Retrieves order items, totals, and masked shipping information; requires a personal Key |
| Tracking | `tvcmall_get_tracking_info` | Retrieves tracking history and order shipping cost for one order; requires a personal Key |
| Tracking | `tvcmall_batch_get_tracking` | Retrieves tracking for multiple orders within the current schema limits; requires a personal Key |
| Points | `tvcmall_get_points` | Retrieves the remaining points without rounding decimal values; requires a personal Key |
| Balance | `tvcmall_get_balance` | Retrieves the backend-formatted current balance; requires a personal Key |
| Balance | `tvcmall_list_balance_records` | Lists balance ledger records; requires a personal Key |

When any TVCMall MCP tool returns a relative image path, the Skill displays it from `https://img.tvc-mall.com/`. Absolute HTTP and HTTPS image URLs remain unchanged.

The Skill does not support placing orders, making payments, cancelling orders, changing addresses, redeeming points, or exporting files.

## Usage Examples

```text
Use $query-tvcmall-customer-data to list my 10 orders.
Search for SKU 100001234A and show the product details.
How many products were added today?
Find black cases for iPhone 17 Pro.
Estimate shipping for 2 units of this product to the United States.
Show tracking status for my recently shipped orders.
Show my remaining points.
Show my current balance.
Show my recent balance expense records.
```

## Security

- Never commit a real personal `TVCMALL_API_KEY` to Git, and never put it in chat, command-line arguments, environment variables, piped input, an Agent client's embedded PTY, logs, errors, or screenshots. Enter it only in the native masked Windows dialog or at the hidden prompt of the Python fallback running in a visible system terminal.
- Treat `config.toml.bak` as sensitive because it contains the immediately previous plaintext configuration; each changed setup replaces this fixed backup instead of accumulating credential copies.
- Use the complete personal PAT as `TVCMALL_API_KEY`; do not add a `Bearer ` prefix.
- Do not configure an `Authorization` header for the inbound MCP connection.
- Each user must use their own Key. Do not use a website password, website login token, OAuth token, or shared credential.
- Do not attempt to recover customer information that the server has masked.
- Use the full endpoint `https://openai.tvc-mall.com/mcp`; do not fall back to HTTP, remove `/mcp`, or append a second `/mcp`.

## Validation

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillValidator = Join-Path $codexHome "skills/.system/skill-creator/scripts/quick_validate.py"
python -X utf8 $skillValidator .agents\skills\query-tvcmall-customer-data
python -m unittest discover -s tests -v
python -m py_compile .agents\skills\query-tvcmall-customer-data\scripts\configure_tvcmall_mcp.py
rg -n -F 'https://openai.tvc-mall.com/mcp' README.md .agents\skills\query-tvcmall-customer-data
git diff --check
```

## Contributing

When adding or modifying a Skill:

1. Follow the standard `SKILL.md`, `agents/openai.yaml`, `scripts/`, and `references/` structure;
2. Add or update tests for scripts and Skill contracts;
3. Update this README's Skills table and capability list;
4. Keep real credentials and customer data out of the repository;
5. Run the complete validation suite before committing.

## Related Links

- [TVCMall MCP](https://github.com/tvcmall-dev/mcp)
- [Apply for a TVCMALL_API_KEY](https://www.tvcmall.com/user/agentkeys)
- [OpenAI Skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI MCP](https://learn.chatgpt.com/docs/extend/mcp)
