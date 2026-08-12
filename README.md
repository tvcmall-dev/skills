# TVCMall Skills

A collection of reusable Codex Skills for TVCMall business scenarios. The current Skill provides read-only customer-data queries through the TVCMall Customer MCP and guides first-time MCP connection plus personal `TVCMALL_API_KEY` configuration.

## Skills

| Skill | Capabilities |
| --- | --- |
| `query-tvcmall-customer-data` | Products, pre-order shipping estimates, Orders, Tracking, Points, and Balance queries; guides MCP setup on first use |

## Requirements

- A mainstream agent tool that supports repository Skills and MCP, such as Codex CLI, Claude Code CLI, Gemini CLI, or GitHub Copilot CLI;
- Python 3.11 or later;
- A personal `TVCMALL_API_KEY`.

## Agent Tool Installation

Install one supported agent tool before cloning this repository. Always prefer the linked official documentation when a package manager, operating system, or authentication method differs from the examples below.

| Tool | Common Installation | Official Documentation |
| --- | --- | --- |
| Codex CLI | `curl -fsSL https://chatgpt.com/codex/install.sh | sh`; Windows: `powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"`; npm: `npm install -g @openai/codex` | [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) |
| Claude Code / Claude Code CLI | `curl -fsSL https://claude.ai/install.sh | bash`; Windows: `irm https://claude.ai/install.ps1 | iex`; WinGet: `winget install Anthropic.ClaudeCode`; npm: `npm install -g @anthropic-ai/claude-code` | [Claude Code setup](https://code.claude.com/docs/en/setup) |
| Gemini CLI | `npm install -g @google/gemini-cli` | [Gemini CLI installation](https://geminicli.com/docs/get-started/installation/) |
| GitHub Copilot CLI | `npm install -g @github/copilot`; Windows: `winget install GitHub.Copilot` | [Install GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli) |
| Cursor CLI | `curl https://cursor.com/install -fsS | bash`; Windows: `irm 'https://cursor.com/install?win32=true' | iex` | [Cursor CLI installation](https://cursor.com/docs/cli/installation) |
| Qwen Code CLI | `curl -fsSL https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.sh | bash`; Windows: `irm https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.ps1 | iex` | [Qwen Code overview](https://qwenlm.github.io/qwen-code-docs/en/users/overview/) |

## Skill Installation and Discovery

```powershell
git clone https://github.com/tvcmall-dev/skills.git
cd skills
codex
```

When an agent starts from the repository directory, it discovers the repository-level Skill under `.agents/skills`. You do not need to clone, build, or run the TVCMall MCP Server locally; this Skill connects to the remote Streamable HTTP MCP.

## First-Time Setup

The canonical TVCMall MCP endpoint is `https://openai.tvc-mall.com/mcp`. The `/mcp` path is part of the endpoint; do not remove it or append it a second time.

1. Invoke `$query-tvcmall-customer-data` in Codex, or ask a TVCMall query directly.
2. The Skill checks whether the current session provides the `tvcmall` MCP and expected tools.
3. If the MCP is not installed, the Skill follows the connection method documented by [TVCMall MCP](https://github.com/tvcmall-dev/mcp) and registers the remote MCP without running a local server.
4. If you do not have a personal `TVCMALL_API_KEY`, sign in and apply at https://www.tvcmall.com/user/agentkeys.
5. After you explicitly confirm plaintext storage, the local script reads the Key through a terminal prompt with input echo disabled and updates the user-level Codex `config.toml`.
6. Restart Codex or start a new session, then check the `tvcmall` tools and call `tvcmall_auth_status`.

The generated configuration looks like this. `<TVCMALL_PAT>` is a placeholder only:

```toml
[mcp_servers.tvcmall]
url = "https://openai.tvc-mall.com/mcp"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

The Key is stored in plaintext in the user-level Codex configuration by the current design. The default path is `%USERPROFILE%\.codex\config.toml` on Windows and `~/.codex/config.toml` on macOS and Linux. If `CODEX_HOME` is set, the script uses `config.toml` under that directory.

## Complete Capability List

All business capabilities are read-only. Detailed parameters, defaults, and WebApi mappings are documented in [Tool Parameter Reference](.agents/skills/query-tvcmall-customer-data/references/tool-reference.md).

| Category | Tool | External Parameters | Capability |
| --- | --- | --- | --- |
| Auth | `tvcmall_auth_status` | None | Checks whether the current MCP session loaded a Key; it does not validate whether the Key is authorized |
| Products | `tvcmall_search_products` | `query`, `page`, `page_size` | Searches products by SKU or keyword with pagination |
| Products | `tvcmall_get_product_detail` | `product_id` | Retrieves one product detail record; the ID must come from search results |
| Shipping | `tvcmall_estimate_shipping` | `sku`, `quantity`, `countrycode` | Estimates pre-order shipping cost for a product |
| Orders | `tvcmall_list_orders` | `start_date`, `end_date`, `status`, `page`, `page_size` | Lists orders with pagination |
| Orders | `tvcmall_get_order_detail` | `order_id` | Retrieves order items, totals, and masked shipping information |
| Tracking | `tvcmall_get_tracking_info` | `order_id` | Retrieves tracking history and order shipping cost for one order |
| Tracking | `tvcmall_batch_get_tracking` | `order_ids` | Retrieves tracking for 1 to 50 orders |
| Points | `tvcmall_get_points` | None | Retrieves the points summary |
| Points | `tvcmall_list_point_records` | `direction`, `page`, `page_size` | Lists points ledger records with pagination |
| Balance | `tvcmall_list_balance_records` | `direction`, `page`, `page_size` | Lists balance ledger records with pagination |

The Skill does not support placing orders, making payments, cancelling orders, changing addresses, redeeming points, or exporting files.

## Usage Examples

```text
Use $query-tvcmall-customer-data to list my 10 orders.
Search for SKU 100001234A and show the product details.
Estimate shipping for 2 units of this product to the United States.
Show tracking status for my recently shipped orders.
Show my points summary and recent points records.
Show my recent balance expense records.
```

## Security

- Never commit a real `TVCMALL_API_KEY` to Git, and never put it in chat, command arguments, logs, or screenshots.
- Use the complete personal PAT as `TVCMALL_API_KEY`; do not add a `Bearer ` prefix.
- Do not configure an `Authorization` header for the inbound MCP connection.
- Each user must use their own Key. Do not use a website password, website login token, OAuth token, or shared credential.
- Do not attempt to recover customer information that the server has masked.
- Use the full endpoint `https://openai.tvc-mall.com/mcp`; do not fall back to HTTP, remove `/mcp`, or append a second `/mcp`.

## Validation

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
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
