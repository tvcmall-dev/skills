# English Skill Content Design

## Goal

Convert the current TVCMall Skill's user-facing documentation and agent instructions from Chinese to English while preserving its behavior, security boundaries, and MCP configuration contract.

## Scope

Translate these files:

- `README.md`
- `.agents/skills/query-tvcmall-customer-data/SKILL.md`
- `.agents/skills/query-tvcmall-customer-data/references/mcp-setup.md`
- `.agents/skills/query-tvcmall-customer-data/references/tool-routing.md`
- `tests/test_skill_contract.py`, only where assertions encode the expected documentation language

Keep these files unchanged:

- `AGENTS.md`, per the user's instruction
- `.agents/skills/query-tvcmall-customer-data/agents/openai.yaml`, because it is already English
- `.agents/skills/query-tvcmall-customer-data/scripts/configure_tvcmall_mcp.py`, because it is already English and its behavior is not changing
- Historical specifications and plans under `docs/superpowers/`

## Translation Rules

- Preserve all URLs, commands, paths, YAML and TOML keys, placeholders, MCP server identifiers, MCP tool names, status values, error codes, and code blocks exactly.
- Preserve the canonical endpoint as `https://mcpserver.tvc-mall.com`; do not append `/mcp` and do not introduce an HTTP fallback.
- Preserve the plaintext user-level Codex configuration model and the terminal no-echo API Key entry workflow.
- Preserve the read-only business boundary and all credential-handling safeguards.
- Use concise, natural technical English rather than a literal word-for-word translation.

## Testing

Update contract assertions before translating the documents so the changed test fails against the current Chinese content. Then translate the scoped files and verify:

- The complete unit test suite passes.
- The Skill validator passes.
- The Python configuration script compiles.
- The canonical endpoint is present and the former endpoint is absent.
- No plausible real TVCMall PAT is present in tracked content.
- `git diff --check` reports no whitespace errors.

## Non-Goals

- No MCP behavior, installation flow, API routing, or security-policy changes.
- No translation of `AGENTS.md` or historical implementation records.
- No new Skill, script, dependency, or MCP endpoint.
