# TVCMall Skills

A collection of Codex Skills for TVCMall business scenarios. The current Skill provides read-only customer data queries through the TVCMall Customer MCP and guides users through MCP connection and personal API Key configuration on first use.

## Skills

| Skill | Capabilities |
| --- | --- |
| `query-tvcmall-customer-data` | Products, pre-order shipping estimates, Orders, Tracking, Points, and Balance queries; guides MCP configuration on first use |

## Requirements

- Codex CLI, IDE extension, or desktop app;
- Python 3.11 or later;
- A personal `TVCMALL_API_KEY`.

## Installation and Discovery

```powershell
git clone https://github.com/tvcmall-dev/skills.git
cd skills
codex
```

When Codex starts from the repository directory, it discovers the repository-level Skill under `.agents/skills`. You do not need to clone, build, or run the TVCMall MCP Server locally; the Skill connects to the remote Streamable HTTP MCP.

## First-Time Setup

The canonical TVCMall MCP endpoint is `https://mcpserver.tvc-mall.com`.

1. Invoke `$query-tvcmall-customer-data` in Codex or ask a TVCMall question.
2. The Skill checks whether the `tvcmall` MCP is available.
3. If it is not installed, the Skill follows the connection instructions from [TVCMall MCP](https://github.com/tvcmall-dev/mcp) to register the remote connection without running the MCP Server locally.
4. If you do not have a personal `TVCMALL_API_KEY`, apply for one at https://www.tvcmall.com/user/agentkeys.
5. After you confirm plaintext storage, the local script reads the Key through a terminal prompt with input echo disabled and updates the user-level Codex `config.toml`.
6. Restart Codex or start a new session, then check the `tvcmall` tools again.

The resulting configuration is shown below. `<TVCMALL_PAT>` is a placeholder only:

```toml
[mcp_servers.tvcmall]
url = "https://mcpserver.tvc-mall.com"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

Under the current design, the Key is stored in plaintext in the user-level Codex configuration. The default path is `%USERPROFILE%\.codex\config.toml` on Windows and `~/.codex/config.toml` on macOS and Linux. If `CODEX_HOME` is set, its `config.toml` is used instead.

## Usage Examples

```text
Use $query-tvcmall-customer-data to list my 10 most recent orders.
Search for the product with SKU 100001234A and show its details.
Estimate shipping for 2 units of this product to the United States.
Show the tracking status for my recently shipped orders.
Show my points summary and recent points records.
Show my recent balance expense records.
```

Current capabilities are read-only and cover Products, shipping for products not yet ordered, Orders, Tracking, Points, and Balance records. The Skill does not support placing orders, making payments, cancelling orders, changing addresses, redeeming points, or exporting files.

## Security

- Never commit a real `TVCMALL_API_KEY` to Git or put it in chat, command arguments, logs, or screenshots.
- Use the complete personal PAT as `TVCMALL_API_KEY`; do not add a `Bearer ` prefix.
- Do not configure an `Authorization` header for the inbound MCP connection.
- Each user must use their own Key. Do not use a website password, website login token, OAuth token, or shared credential.
- Do not attempt to recover customer information that the server has masked.
- Keep the endpoint on the canonical HTTPS address. Do not fall back to HTTP or append `/mcp` if the connection fails.

## Validation

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
python -m unittest discover -s tests -v
rg -n -F 'https://mcpserver.tvc-mall.com' README.md .agents\skills\query-tvcmall-customer-data
git diff --check
```

## Contributing

When adding or modifying a Skill:

1. Follow the standard `SKILL.md`, `agents/openai.yaml`, `scripts/`, and `references/` structure;
2. Add or update tests for scripts and Skill contracts;
3. Update the Skills table in this README;
4. Keep real credentials and customer data out of the repository;
5. Run the complete validation suite before committing.

## Related Links

- [TVCMall MCP](https://github.com/tvcmall-dev/mcp)
- [Apply for a TVCMALL_API_KEY](https://www.tvcmall.com/user/agentkeys)
- [OpenAI Skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI MCP](https://learn.chatgpt.com/docs/extend/mcp)
