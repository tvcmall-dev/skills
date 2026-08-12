# AGENTS.md

## Scope

- This repository contains reusable TVCMall Codex Skills under `.agents/skills/`.
- Keep each Skill self-contained and compatible with the OpenAI Skill specification.

## Security

- Never commit a real `TVCMALL_API_KEY`, customer data, or a user-level Codex `config.toml`.
- Use `https://mcpserver.tvc-mall.com` exactly; do not add `/mcp` or fall back to HTTP.
- Do not print API keys in logs, errors, tests, or final responses.
- TVCMall business access is read-only unless a separately approved design changes that boundary.

## Development

- Use Chinese for project documentation and user-facing Skill instructions; keep identifiers and protocol fields in their original form.
- Add or update tests for scripts and Skill contracts.
- Run the Skill validator, unit tests, secret scan, and `git diff --check` before completion.
