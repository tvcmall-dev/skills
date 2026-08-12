# TVCMall Customer Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a standard repository-scoped Codex Skill that configures the TVCMall remote MCP safely and routes read-only customer queries to the correct MCP tools.

**Architecture:** Keep one concise `query-tvcmall-customer-data` Skill as the entry point. Put deterministic Codex TOML inspection/update behavior in a Python standard-library script, detailed setup and routing rules in one-level reference files, and user-facing installation/security guidance in the repository root README.

**Tech Stack:** Codex Skill format (`SKILL.md`, `agents/openai.yaml`), Python 3.11+ standard library (`argparse`, `getpass`, `pathlib`, `re`, `shutil`, `tempfile`, `tomllib`), `unittest`, Git.

---

## File Map

- Create `.agents/skills/query-tvcmall-customer-data/SKILL.md`: concise trigger-time workflow, safety gates, and links to bundled resources.
- Create `.agents/skills/query-tvcmall-customer-data/agents/openai.yaml`: user-facing metadata and the `tvcmall` Streamable HTTP MCP dependency.
- Create `.agents/skills/query-tvcmall-customer-data/scripts/configure_tvcmall_mcp.py`: inspect and update Codex user configuration without printing the Key.
- Create `.agents/skills/query-tvcmall-customer-data/references/mcp-setup.md`: detailed first-run, Key acquisition, restart, and error flow.
- Create `.agents/skills/query-tvcmall-customer-data/references/tool-routing.md`: MCP tool selection, multi-tool workflows, output, and error rules.
- Create `tests/test_configure_tvcmall_mcp.py`: isolated unit and CLI tests using temporary config files only.
- Create `tests/test_skill_contract.py`: static contract tests for Skill metadata, endpoint, README, and secret safety.
- Create `README.md`: standard repository overview, installation/discovery, setup, examples, validation, and contribution guide.
- Create `AGENTS.md`: stable repository rules for future Skill development.
- Create `.gitignore`: ignore Python caches, virtual environments, coverage files, local config, and test artifacts.
- Modify `docs/superpowers/plans/2026-08-12-tvcmall-customer-skill.md`: check off steps during execution.

### Task 1: Create the standard repository and Skill skeleton

**Files:**
- Create: `.gitignore`
- Create: `AGENTS.md`
- Create: `.agents/skills/query-tvcmall-customer-data/SKILL.md`
- Create: `.agents/skills/query-tvcmall-customer-data/agents/openai.yaml`
- Create: `.agents/skills/query-tvcmall-customer-data/scripts/`
- Create: `.agents/skills/query-tvcmall-customer-data/references/`

- [x] **Step 1: Generate the official Skill skeleton**

Run:

```powershell
python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\init_skill.py `
  query-tvcmall-customer-data `
  --path .agents\skills `
  --resources scripts,references `
  --interface 'display_name=TVCMall Customer Query' `
  --interface 'short_description=Query TVCMall products, orders, shipping, points, and balance' `
  --interface 'default_prompt=Use $query-tvcmall-customer-data to check my recent TVCMall orders and tracking status.'
```

Expected: the generator creates `SKILL.md`, `agents/openai.yaml`, `scripts/`, and `references/` under `.agents/skills/query-tvcmall-customer-data` without example placeholder files.

- [x] **Step 2: Add repository hygiene files**

Create `.gitignore` with:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
.venv/
venv/
.env
.env.*
!.env.example
config.toml
*.bak
*.tmp
```

Create `AGENTS.md` with these stable rules:

```markdown
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
```

- [x] **Step 3: Replace generated placeholders with a valid minimal Skill**

Replace `SKILL.md` with a minimal valid file so the repository never commits generated markers:

```markdown
---
name: query-tvcmall-customer-data
description: Configure and use the TVCMall Customer MCP for read-only product, shipping, order, tracking, points, and balance queries. Use when Codex needs to install or repair the tvcmall MCP connection, configure TVCMALL_API_KEY, or answer TVCMall customer-data questions.
---

# TVCMall Customer Data

Use the `tvcmall` MCP dependency for TVCMall read-only customer queries.

Before a business query, confirm the dependency is available and follow [references/mcp-setup.md](references/mcp-setup.md) when setup is required. Read [references/tool-routing.md](references/tool-routing.md) before selecting business tools.
```

- [x] **Step 4: Run the template validator**

Run:

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
```

Expected: `Skill is valid!`

- [x] **Step 5: Commit the skeleton**

```powershell
git add .gitignore AGENTS.md .agents/skills/query-tvcmall-customer-data
git commit -m "chore: scaffold TVCMall customer skill"
```

### Task 2: Implement the pure Codex config transformation with TDD

**Files:**
- Create: `tests/test_configure_tvcmall_mcp.py`
- Create: `.agents/skills/query-tvcmall-customer-data/scripts/configure_tvcmall_mcp.py`

- [x] **Step 1: Write failing tests for Key validation and TOML escaping**

Create the test module and load the hyphenated Skill script by path:

```python
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/query-tvcmall-customer-data/scripts/configure_tvcmall_mcp.py"
SPEC = importlib.util.spec_from_file_location("configure_tvcmall_mcp", SCRIPT)
assert SPEC and SPEC.loader
configurer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = configurer
SPEC.loader.exec_module(configurer)


class ValidationTests(unittest.TestCase):
    def test_accepts_pat_shape(self) -> None:
        self.assertEqual(configurer.validate_api_key("tmcp_v1_demo.secret"), "tmcp_v1_demo.secret")

    def test_rejects_whitespace_and_bearer_prefix(self) -> None:
        for value in (" tmcp_v1_demo.secret", "tmcp_v1_demo.secret ", "Bearer tmcp_v1_demo.secret"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                configurer.validate_api_key(value)

    def test_toml_string_escapes_quotes_and_backslashes(self) -> None:
        self.assertEqual(configurer.toml_string('a"b\\c'), '"a\\"b\\\\c"')
```

- [x] **Step 2: Run the validation tests and verify RED**

Run:

```powershell
python -m unittest tests.test_configure_tvcmall_mcp.ValidationTests -v
```

Expected: FAIL because `configure_tvcmall_mcp.py` or its functions do not exist.

- [x] **Step 3: Implement Key validation and TOML string encoding**

Create the script with:

```python
from __future__ import annotations

import re


MCP_URL = "https://mcpserver.tvc-mall.com"
API_KEY_PATTERN = re.compile(r"^tmcp_v1_[^\s.]+\.[^\s.]+$")


def validate_api_key(value: str) -> str:
    if value != value.strip() or not API_KEY_PATTERN.fullmatch(value):
        raise ValueError("TVCMALL_API_KEY must match tmcp_v1_{tokenId}.{secret} without Bearer")
    return value


def toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\b", "\\b").replace("\t", "\\t")
    escaped = escaped.replace("\n", "\\n").replace("\f", "\\f").replace("\r", "\\r")
    return f'"{escaped}"'
```

- [x] **Step 4: Run the validation tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_configure_tvcmall_mcp.ValidationTests -v
```

Expected: 3 tests pass.

- [x] **Step 5: Write failing transformation tests**

Append:

```python
import tomllib


class TransformTests(unittest.TestCase):
    def test_adds_tvcmall_to_empty_config(self) -> None:
        updated = configurer.upsert_tvcmall_config("", "tmcp_v1_demo.secret")
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["mcp_servers"]["tvcmall"]["url"], configurer.MCP_URL)
        self.assertEqual(parsed["mcp_servers"]["tvcmall"]["http_headers"]["TVCMALL_API_KEY"], "tmcp_v1_demo.secret")

    def test_preserves_other_servers_and_replaces_tvcmall_subtables(self) -> None:
        source = '''model = "gpt-5"

[mcp_servers.other]
url = "https://example.com/mcp"

[mcp_servers.tvcmall]
url = "http://old.invalid/mcp"

[mcp_servers.tvcmall.http_headers]
OLD = "value"
'''
        updated = configurer.upsert_tvcmall_config(source, "tmcp_v1_demo_new.secret")
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["model"], "gpt-5")
        self.assertEqual(parsed["mcp_servers"]["other"]["url"], "https://example.com/mcp")
        self.assertEqual(set(parsed["mcp_servers"]["tvcmall"]), {"url", "http_headers"})
        self.assertEqual(updated.count("[mcp_servers.tvcmall]"), 1)

    def test_replaces_equivalent_quoted_tvcmall_tables(self) -> None:
        source = '''[mcp_servers."tvcmall"]
url = "https://old.invalid"

[mcp_servers."tvcmall".http_headers]
OLD = "value"
'''
        updated = configurer.upsert_tvcmall_config(source, "tmcp_v1_demo.secret")
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["mcp_servers"]["tvcmall"]["url"], configurer.MCP_URL)
        self.assertNotIn("OLD", parsed["mcp_servers"]["tvcmall"]["http_headers"])
        self.assertEqual(updated.count("[mcp_servers.tvcmall]"), 1)

    def test_rejects_invalid_existing_toml(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid TOML"):
            configurer.upsert_tvcmall_config("[broken", "tmcp_v1_demo.secret")

    def test_repeated_transform_is_idempotent(self) -> None:
        first = configurer.upsert_tvcmall_config("", "tmcp_v1_demo.secret")
        second = configurer.upsert_tvcmall_config(first, "tmcp_v1_demo.secret")
        self.assertEqual(second, first)

    def test_crlf_source_remains_valid_and_preserves_other_settings(self) -> None:
        source = 'model = "gpt-5"\r\n\r\n[mcp_servers.other]\r\nurl = "https://example.com/mcp"\r\n'
        updated = configurer.upsert_tvcmall_config(source, "tmcp_v1_demo.secret")
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["model"], "gpt-5")
        self.assertEqual(parsed["mcp_servers"]["other"]["url"], "https://example.com/mcp")
        self.assertNotIn("\n", updated.replace("\r\n", ""))

    def test_source_without_terminal_newline_stays_valid(self) -> None:
        updated = configurer.upsert_tvcmall_config('model = "gpt-5"', "tmcp_v1_demo.secret")
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["model"], "gpt-5")
        self.assertEqual(parsed["mcp_servers"]["tvcmall"]["url"], configurer.MCP_URL)
```

- [x] **Step 6: Run transformation tests and verify RED**

Run:

```powershell
python -m unittest tests.test_configure_tvcmall_mcp.TransformTests -v
```

Expected: FAIL because `upsert_tvcmall_config` is not defined.

- [x] **Step 7: Implement section-aware replacement**

Add `import tomllib` and implement:

```python
TV_TABLE = "mcp_servers.tvcmall"
TABLE_HEADER_PATTERN = re.compile(r"(?m)^\s*\[([^\]\r\n]+)\]\s*(?:#.*)?$")


def _is_tvcmall_table(name: str) -> bool:
    marker = "__tvcmall_config_marker__"
    try:
        parsed = tomllib.loads(f"[{name}]\n{marker} = true\n")
    except tomllib.TOMLDecodeError:
        return False

    def marker_path(value: object, path: tuple[str, ...] = ()) -> tuple[str, ...] | None:
        if not isinstance(value, dict):
            return None
        if value.get(marker) is True:
            return path
        for key, child in value.items():
            found = marker_path(child, (*path, key))
            if found is not None:
                return found
        return None

    path = marker_path(parsed)
    return path is not None and path[:2] == ("mcp_servers", "tvcmall")


def _remove_tvcmall_tables(source: str) -> str:
    matches = list(TABLE_HEADER_PATTERN.finditer(source))
    ranges: list[tuple[int, int]] = []
    for index, match in enumerate(matches):
        if _is_tvcmall_table(match.group(1)):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
            ranges.append((match.start(), end))
    for start, end in reversed(ranges):
        source = source[:start] + source[end:]
    return source.rstrip()


def upsert_tvcmall_config(source: str, api_key: str) -> str:
    api_key = validate_api_key(api_key)
    try:
        tomllib.loads(source)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError("Existing Codex config must be valid TOML") from exc

    newline = "\r\n" if "\r\n" in source else "\n"
    base = _remove_tvcmall_tables(source)
    section = (
        f"[mcp_servers.tvcmall]{newline}"
        f"url = {toml_string(MCP_URL)}{newline}"
        f"http_headers = {{ \"TVCMALL_API_KEY\" = {toml_string(api_key)} }}{newline}"
    )
    updated = f"{base}{newline}{newline}{section}" if base else section
    tomllib.loads(updated)
    return updated
```

- [x] **Step 8: Run all pure-function tests**

Run:

```powershell
python -m unittest tests.test_configure_tvcmall_mcp.ValidationTests tests.test_configure_tvcmall_mcp.TransformTests -v
```

Expected: 10 tests pass. Final implementation adds two hardening tests for control-character escaping and file-level CRLF preservation.

- [x] **Step 9: Commit the pure transformation**

```powershell
git add tests/test_configure_tvcmall_mcp.py .agents/skills/query-tvcmall-customer-data/scripts/configure_tvcmall_mcp.py
git commit -m "feat: transform Codex TVCMall MCP config"
```

### Task 3: Add safe file update and interactive CLI with TDD

**Files:**
- Modify: `tests/test_configure_tvcmall_mcp.py`
- Modify: `.agents/skills/query-tvcmall-customer-data/scripts/configure_tvcmall_mcp.py`

- [x] **Step 1: Write failing file-update tests**

Append imports and tests:

```python
import contextlib
import io
import os
import subprocess
import sys
import tempfile
from unittest import mock


class FileUpdateTests(unittest.TestCase):
    def test_creates_backup_and_preserves_other_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            original = '[mcp_servers.other]\nurl = "https://example.com/mcp"\n'
            path.write_text(original, encoding="utf-8")
            result = configurer.configure_file(path, "tmcp_v1_demo.secret")
            self.assertTrue(result.changed)
            self.assertEqual(result.backup_path.read_text(encoding="utf-8"), original)
            parsed = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertIn("other", parsed["mcp_servers"])
            self.assertIn("tvcmall", parsed["mcp_servers"])

    def test_invalid_toml_does_not_change_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text("[broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                configurer.configure_file(path, "tmcp_v1_demo.secret")
            self.assertEqual(path.read_text(encoding="utf-8"), "[broken")
            self.assertFalse(path.with_name("config.toml.bak").exists())

    def test_idempotent_update_does_not_create_a_new_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            first = configurer.configure_file(path, "tmcp_v1_demo.secret")
            second = configurer.configure_file(path, "tmcp_v1_demo.secret")
            self.assertTrue(first.changed)
            self.assertFalse(second.changed)
            self.assertIsNone(second.backup_path)

    def test_write_failure_keeps_original(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            original = 'model = "gpt-5"\n'
            path.write_text(original, encoding="utf-8")
            with mock.patch.object(configurer.os, "replace", side_effect=OSError("blocked")):
                with self.assertRaises(OSError):
                    configurer.configure_file(path, "tmcp_v1_demo.secret")
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_read_only_destination_failure_keeps_original(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            original = 'model = "gpt-5"\n'
            path.write_text(original, encoding="utf-8")
            with mock.patch.object(configurer.tempfile, "mkstemp", side_effect=PermissionError("read only")):
                with self.assertRaises(PermissionError):
                    configurer.configure_file(path, "tmcp_v1_demo.secret")
            self.assertEqual(path.read_text(encoding="utf-8"), original)
```

- [x] **Step 2: Run file-update tests and verify RED**

Run:

```powershell
python -m unittest tests.test_configure_tvcmall_mcp.FileUpdateTests -v
```

Expected: FAIL because `configure_file` and the result type do not exist.

- [x] **Step 3: Implement backup and atomic replacement**

Add imports and types:

```python
import os
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile


@dataclass(frozen=True)
class ConfigureResult:
    config_path: Path
    backup_path: Path | None
    changed: bool
```

Add:

```python
def configure_file(config_path: Path, api_key: str) -> ConfigureResult:
    source = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    updated = upsert_tvcmall_config(source, api_key)
    if updated == source:
        return ConfigureResult(config_path, None, False)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path: Path | None = None
    if config_path.exists():
        backup_path = config_path.with_name(f"{config_path.name}.bak")
        shutil.copy2(config_path, backup_path)

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{config_path.name}.", suffix=".tmp", dir=config_path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, config_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return ConfigureResult(config_path, backup_path, True)
```

- [x] **Step 4: Run file-update tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_configure_tvcmall_mcp.FileUpdateTests -v
```

Expected: 5 tests pass.

- [x] **Step 5: Write failing CLI tests**

Append:

```python
class CliTests(unittest.TestCase):
    def test_resolve_config_path_prefers_codex_home(self) -> None:
        with mock.patch.dict(os.environ, {"CODEX_HOME": "C:/tmp/codex-home"}, clear=True):
            self.assertEqual(configurer.resolve_config_path(), Path("C:/tmp/codex-home/config.toml"))

    def test_main_reads_key_with_getpass_and_does_not_print_it(self) -> None:
        secret = "tmcp_v1_fake.secret"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch.object(configurer.getpass, "getpass", return_value=secret):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code = configurer.main(["--config", str(path), "--yes"])
            self.assertEqual(code, 0)
            self.assertNotIn(secret, stdout.getvalue() + stderr.getvalue())
            self.assertIn(secret, path.read_text(encoding="utf-8"))

    def test_main_rejects_invalid_key_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            stderr = io.StringIO()
            with mock.patch.object(configurer.getpass, "getpass", return_value="invalid"):
                with contextlib.redirect_stderr(stderr):
                    code = configurer.main(["--config", str(path), "--yes"])
            self.assertEqual(code, 2)
            self.assertFalse(path.exists())
            self.assertNotIn("invalid", stderr.getvalue())
```

- [x] **Step 6: Run CLI tests and verify RED**

Run:

```powershell
python -m unittest tests.test_configure_tvcmall_mcp.CliTests -v
```

Expected: FAIL because `resolve_config_path`, `getpass`, and `main` do not exist.

- [x] **Step 7: Implement the no-echo CLI**

Add imports:

```python
import argparse
import getpass
import sys
from collections.abc import Sequence
```

Add:

```python
def resolve_config_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home) if codex_home else Path.home() / ".codex") / "config.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure the TVCMall remote MCP for Codex")
    parser.add_argument("--config", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--yes", action="store_true", help="confirm plaintext storage without an interactive yes/no prompt")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = resolve_config_path(args.config)
    if not args.yes:
        print(f"TVCMALL_API_KEY will be stored in plaintext at {config_path}.")
        if input("Continue? [y/N] ").strip().lower() not in {"y", "yes"}:
            print("Configuration cancelled.")
            return 1
    try:
        api_key = validate_api_key(getpass.getpass("TVCMALL_API_KEY: "))
        result = configure_file(config_path, api_key)
    except (OSError, ValueError) as exc:
        print(f"Configuration failed: {exc}", file=sys.stderr)
        return 2

    state = "updated" if result.changed else "already current"
    print(f"TVCMall MCP configuration {state}: {result.config_path}")
    if result.backup_path:
        print(f"Backup created: {result.backup_path}")
    print("Restart Codex or start a new session, then verify the tvcmall MCP tools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 8: Run the complete script test suite**

Run:

```powershell
python -m unittest tests.test_configure_tvcmall_mcp -v
```

Expected: 18 tests pass and no test touches the real user config. Final implementation adds two hardening tests after this planned checkpoint.

- [x] **Step 9: Compile the script**

Run:

```powershell
python -m py_compile .agents\skills\query-tvcmall-customer-data\scripts\configure_tvcmall_mcp.py
```

Expected: exit 0 with no output.

- [x] **Step 10: Commit file safety and CLI**

```powershell
git add tests/test_configure_tvcmall_mcp.py .agents/skills/query-tvcmall-customer-data/scripts/configure_tvcmall_mcp.py
git commit -m "feat: configure TVCMall MCP for Codex"
```

### Task 4: Write the Skill instructions, references, and MCP metadata

**Files:**
- Modify: `.agents/skills/query-tvcmall-customer-data/SKILL.md`
- Modify: `.agents/skills/query-tvcmall-customer-data/agents/openai.yaml`
- Create: `.agents/skills/query-tvcmall-customer-data/references/mcp-setup.md`
- Create: `.agents/skills/query-tvcmall-customer-data/references/tool-routing.md`
- Create: `tests/test_skill_contract.py`

- [x] **Step 1: Write failing contract tests**

Create:

```python
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/query-tvcmall-customer-data"
ENDPOINT = "https://mcpserver.tvc-mall.com"


class SkillContractTests(unittest.TestCase):
    def test_frontmatter_contains_only_name_and_description(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        keys = re.findall(r"^([a-z_]+):", frontmatter, re.MULTILINE)
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("configure TVCMALL_API_KEY", frontmatter)

    def test_openai_yaml_declares_exact_tvcmall_dependency(self) -> None:
        text = (SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
        self.assertIn('value: "tvcmall"', text)
        self.assertIn('transport: "streamable_http"', text)
        self.assertIn(f'url: "{ENDPOINT}"', text)
        self.assertIn("$query-tvcmall-customer-data", text)

    def test_skill_links_both_references_and_setup_script(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for relative in ("references/mcp-setup.md", "references/tool-routing.md", "scripts/configure_tvcmall_mcp.py"):
            self.assertIn(relative, text)
            self.assertTrue((SKILL / relative).exists())

    def test_no_old_endpoint_or_plausible_real_pat(self) -> None:
        deliverables = [ROOT / "README.md", ROOT / "AGENTS.md", *SKILL.rglob("*")]
        repository_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in deliverables
            if path.is_file()
        )
        forbidden_host = ".".join(("115", "175", "225", "101"))
        self.assertNotIn(forbidden_host, repository_text)
        leaked = re.findall(r"tmcp_v1_(?!demo|fake|example)[^\s.]+\.[^\s\"'<>]+", repository_text)
        self.assertEqual(leaked, [])
```

- [x] **Step 2: Run contract tests and verify RED**

Run:

```powershell
python -m unittest tests.test_skill_contract -v
```

Expected: FAIL because the complete references and metadata do not exist yet.

- [x] **Step 3: Write `mcp-setup.md`**

Include these exact sections and rules:

```markdown
# TVCMall MCP Setup

## Setup Decision

1. Check whether the `tvcmall` dependency and expected tools are available.
2. If available, call `tvcmall_auth_status`; do not reinstall automatically.
3. If missing, explain that setup registers a remote MCP connection in the user's Codex config.

## API Key

- Ask whether the user already has `TVCMALL_API_KEY`.
- If not, direct the user to https://www.tvcmall.com/user/agentkeys and wait.
- Do not ask the user to paste the Key into chat.
- Explain that the selected setup stores the Key in plaintext in the user-level Codex `config.toml`.

## Configure

After explicit confirmation, run `python scripts/configure_tvcmall_mcp.py` from this Skill directory. The script securely prompts for the Key without echo and writes:

```toml
[mcp_servers.tvcmall]
url = "https://mcpserver.tvc-mall.com"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

Never pass the Key as a command-line argument. Never append `/mcp` to the endpoint.

## Restart And Verify

Ask the user to restart Codex or create a new session. Confirm that `tvcmall` tools are visible, then call `tvcmall_auth_status`. Treat `configured: true` as session configuration only; verify permissions through the requested read-only query.

## Setup Errors

- Preserve the original config when TOML is invalid or writing fails.
- For network errors or `5xx`, retain the HTTPS configuration and recommend retrying later.
- Never fall back to HTTP.
```

- [x] **Step 4: Write `tool-routing.md`**

Include the exact tool table from the approved design plus these rules:

```markdown
# TVCMall Tool Routing

## Global Rules

- Use only the `tvcmall` MCP tools as business-data sources.
- Keep every operation read-only and query only the scope requested by the user.
- Do not recover redacted PII, expose raw upstream bodies, or print authentication data.
- Use finite pagination and pass at most 50 order IDs to batch tracking.

## Product And Shipping

| User intent | Tool | Required behavior |
| --- | --- | --- |
| Search by SKU or keyword | `tvcmall_search_products` | Stop on no result; ask the user to choose among multiple matches |
| View one product | `tvcmall_get_product_detail` | Use only a `product_id` returned by search |
| Estimate unplaced-item shipping | `tvcmall_estimate_shipping` | Require SKU, quantity, and a two-letter country code |
| List or filter orders | `tvcmall_list_orders` | Use supported status values and finite pagination |
| View one order | `tvcmall_get_order_detail` | Use a user-provided or tool-returned `order_id` |
| View one placed order's tracking or shipping cost | `tvcmall_get_tracking_info` | Never substitute product shipping estimation |
| View tracking for several current results | `tvcmall_batch_get_tracking` | Pass at most 50 current-result order IDs |
| View points summary | `tvcmall_get_points` | Do not confuse with transaction history |
| View points history | `tvcmall_list_point_records` | Use `all`, `got`, or `used` |
| View balance history | `tvcmall_list_balance_records` | Use `all`, `income`, or `expense` |

## Orders And Tracking

- `tvcmall_list_orders`: list or filter orders with supported status values and finite pages.
- `tvcmall_get_order_detail`: inspect a known order.
- `tvcmall_get_tracking_info`: get one order's tracking or placed-order shipping cost.
- `tvcmall_batch_get_tracking`: get tracking for current-page order IDs, at most 50.
- For recent shipped-order tracking, call `tvcmall_list_orders(status=V3Shipped)` then `tvcmall_batch_get_tracking`.
- Map order-language filters as follows: all=`V3All`, unpaid=`V3Unpaid`, awaiting confirmation=`V3AwaitingConfirmation`, preparing=`V3Preparing`, shipped=`V3Shipped`, done=`V3Done`.

## Points And Balance

- `tvcmall_get_points`: points summary.
- `tvcmall_list_point_records`: points history with `all`, `got`, or `used`.
- `tvcmall_list_balance_records`: balance history with `all`, `income`, or `expense`.

## Stable Errors

- `AUTH_REQUIRED`: configure or replace the Key without asking for it in chat.
- `PERMISSION_DENIED`: explain missing permission or route availability; do not bypass it.
- `RATE_LIMITED`: recommend waiting before retrying.
- `API_UNAVAILABLE`: state that the service is unavailable and do not invent results.
- `SESSION_NOT_FOUND`: reconnect or restart Codex.
```

- [x] **Step 5: Replace `SKILL.md` with the complete imperative workflow**

Replace the complete file with:

```markdown
---
name: query-tvcmall-customer-data
description: Configure and use the TVCMall Customer MCP for read-only product, shipping, order, tracking, points, and balance queries. Use when Codex needs to install or repair the tvcmall MCP connection, configure TVCMALL_API_KEY, or answer TVCMall customer-data questions.
---

# TVCMall Customer Data

## Prepare The MCP

1. Check whether the `tvcmall` MCP dependency and expected tools are available.
2. If setup or repair is needed, read [references/mcp-setup.md](references/mcp-setup.md) completely and follow it.
3. Run [scripts/configure_tvcmall_mcp.py](scripts/configure_tvcmall_mcp.py) only after the user confirms plaintext storage.
4. After setup, require a Codex restart or new session before attempting business tools.

## Route The Request

Read [references/tool-routing.md](references/tool-routing.md) completely before selecting tools. Ask only for parameters required by the selected tool. Use finite queries and stop when the request is satisfied.

## Protect Customer Data

- Keep all actions read-only.
- Never request a Key in chat or print a Key from config, logs, errors, or tool output.
- Never call TVCMall WebApi directly or bypass MCP authorization.
- Return a direct answer followed by the minimum useful structured detail.
```

- [x] **Step 6: Regenerate and extend `agents/openai.yaml`**

First regenerate the interface deterministically:

```powershell
python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\generate_openai_yaml.py `
  .agents\skills\query-tvcmall-customer-data `
  --interface 'display_name=TVCMall Customer Query' `
  --interface 'short_description=Query TVCMall products, orders, shipping, points, and balance' `
  --interface 'default_prompt=Use $query-tvcmall-customer-data to check my recent TVCMall orders and tracking status.'
```

Then add the dependency block:

```yaml
dependencies:
  tools:
    - type: "mcp"
      value: "tvcmall"
      description: "TVCMall Customer MCP for authenticated read-only customer queries"
      transport: "streamable_http"
      url: "https://mcpserver.tvc-mall.com"
```

- [x] **Step 7: Run Skill and contract validation**

Run:

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
python -m unittest tests.test_skill_contract -v
```

Expected: `Skill is valid!` and 4 tests pass.

- [x] **Step 8: Commit the complete Skill contract**

```powershell
git add .agents/skills/query-tvcmall-customer-data tests/test_skill_contract.py
git commit -m "feat: add TVCMall query workflow"
```

### Task 5: Add the standard root README

**Files:**
- Create: `README.md`
- Modify: `tests/test_skill_contract.py`

- [x] **Step 1: Write a failing README contract test**

Append:

```python
    def test_readme_covers_setup_usage_security_and_contributing(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        required = (
            "query-tvcmall-customer-data",
            ENDPOINT,
            "https://www.tvcmall.com/user/agentkeys",
            "TVCMALL_API_KEY",
            "商品",
            "订单",
            "物流",
            "积分",
            "余额",
            "安全",
            "验证",
            "贡献",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)
        self.assertNotIn("115.175.225.101", text)
```

- [x] **Step 2: Run the README test and verify RED**

Run:

```powershell
python -m unittest tests.test_skill_contract.SkillContractTests.test_readme_covers_setup_usage_security_and_contributing -v
```

Expected: FAIL because root `README.md` does not exist.

- [x] **Step 3: Write the standard README**

Create `README.md` with this complete content:

```markdown
# TVCMall Skills

面向 TVCMall 业务场景的 Codex Skills 集合。当前 Skill 通过 TVCMall Customer MCP 提供只读客户数据查询，并在首次使用时引导完成 MCP 连接和个人 API Key 配置。

## Skills

| Skill | 功能 |
| --- | --- |
| `query-tvcmall-customer-data` | 商品、未下单运费、订单、物流、积分和余额查询；首次使用时引导配置 MCP |

## 环境要求

- Codex CLI、IDE extension 或 desktop app；
- Python 3.11 或更高版本；
- 个人 `TVCMALL_API_KEY`。

## 安装与发现

```powershell
git clone https://github.com/tvcmall-dev/skills.git
cd skills
codex
```

从仓库目录启动 Codex 后，Codex 会发现 `.agents/skills` 下的仓库级 Skill。不需要克隆、构建或运行 TVCMall MCP Server；Skill 连接远程 Streamable HTTP MCP。

## 首次配置

TVCMall MCP 的标准 endpoint 是 `https://mcpserver.tvc-mall.com`。

1. 在 Codex 中调用 `$query-tvcmall-customer-data` 或提出 TVCMall 查询。
2. Skill 检查 `tvcmall` MCP 是否已经可用。
3. 如果你没有个人 `TVCMALL_API_KEY`，先前往 https://www.tvcmall.com/user/agentkeys 申请。
4. 确认配置后，本机脚本使用无回显输入读取 Key，并更新 Codex 用户级 `config.toml`。
5. 重启 Codex或新建会话，再检查 `tvcmall` tools。

配置结果如下。`<TVCMALL_PAT>` 仅为占位符：

```toml
[mcp_servers.tvcmall]
url = "https://mcpserver.tvc-mall.com"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

Key 会按照当前设计明文保存在用户级 Codex 配置中。Windows 默认路径为 `%USERPROFILE%\.codex\config.toml`；macOS 和 Linux 默认为 `~/.codex/config.toml`。如设置了 `CODEX_HOME`，则使用其中的 `config.toml`。

## 使用示例

```text
使用 $query-tvcmall-customer-data 查询我最近 10 个订单。
搜索 SKU 为 100001234A 的商品并查看详情。
估算 2 件该商品寄往美国的运费。
查询最近已发货订单的物流状态。
查询我的积分汇总和最近积分流水。
查询最近的余额支出记录。
```

当前能力只读，包括商品、未下单商品运费、订单、物流、积分和余额流水。不支持下单、支付、取消订单、修改地址、积分兑换或文件导出。

## 安全

- 不要把真实 `TVCMALL_API_KEY` 提交到 Git、粘贴到聊天、放进命令参数、日志或截图。
- `TVCMALL_API_KEY` 使用完整个人 PAT，不添加 `Bearer ` 前缀。
- 不要为入站 MCP 连接配置 `Authorization` Header。
- 每位用户使用自己的 Key，不要使用网站密码、网站登录 token、OAuth token 或共享凭据。
- 不要尝试恢复服务端已脱敏的客户信息。

## 验证

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
python -m unittest discover -s tests -v
rg -n -F 'https://mcpserver.tvc-mall.com' README.md .agents\skills\query-tvcmall-customer-data
git diff --check
```

## 贡献

新增或修改 Skill 时：

1. 遵循标准 `SKILL.md`、`agents/openai.yaml`、`scripts/` 和 `references/` 结构；
2. 为脚本和 Skill 合约补充测试；
3. 更新本 README 的 Skills 表；
4. 确保真实凭据与客户数据不进入仓库；
5. 提交前运行完整验证。

## 相关链接

- [TVCMall MCP](https://github.com/tvcmall-dev/mcp)
- [申请 TVCMALL_API_KEY](https://www.tvcmall.com/user/agentkeys)
- [OpenAI Skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI MCP](https://learn.chatgpt.com/docs/extend/mcp)
```

- [x] **Step 4: Run README and all contract tests**

Run:

```powershell
python -m unittest tests.test_skill_contract -v
```

Expected: 5 tests pass.

- [x] **Step 5: Commit README and its contract**

```powershell
git add README.md tests/test_skill_contract.py
git commit -m "docs: add TVCMall Skills README"
```

### Task 6: Run full verification and harden any discovered gaps

**Files:**
- Modify if required: `.agents/skills/query-tvcmall-customer-data/**`
- Modify if required: `README.md`
- Modify if required: `tests/*.py`

- [x] **Step 1: Run all unit and contract tests**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all 32 final tests pass: 23 planned tests plus CRLF preservation, control-character escaping, strict ASCII PAT validation, multiline-string and array-table preservation, concurrent-change detection, backup-path reporting, tracked-file secret scanning, and forward-test gap contracts.

- [x] **Step 2: Validate the Skill package**

Run:

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
```

Expected: `Skill is valid!`

- [x] **Step 3: Verify Python syntax**

Run:

```powershell
python -m py_compile .agents\skills\query-tvcmall-customer-data\scripts\configure_tvcmall_mcp.py tests\test_configure_tvcmall_mcp.py tests\test_skill_contract.py
```

Expected: exit 0 with no output.

- [x] **Step 4: Run repository-wide endpoint and secret scans**

Run:

```powershell
$forbiddenHost = @('115','175','225','101') -join '.'
$deliveryFiles = @('README.md','AGENTS.md') + (rg --files .agents\skills\query-tvcmall-customer-data)
$old = Select-String -LiteralPath $deliveryFiles -SimpleMatch $forbiddenHost
if ($old) { throw "Old endpoint found in delivery files: $($old.Path -join ', ')" }

$leaks = rg -n 'tmcp_v1_(?!demo|fake|example)[^\s.]+\.[^\s"''<>]+' README.md AGENTS.md .agents\skills\query-tvcmall-customer-data --pcre2
if ($LASTEXITCODE -eq 0) { throw "Possible real API key found:`n$leaks" }
if ($LASTEXITCODE -ne 1) { throw "Secret scan failed with exit code $LASTEXITCODE" }

rg -n -F 'https://mcpserver.tvc-mall.com' README.md .agents\skills\query-tvcmall-customer-data
```

Expected: no old endpoint and no plausible real Key; the exact HTTPS endpoint appears in README, metadata, setup reference, and script.

- [x] **Step 5: Check formatting and worktree scope**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only intentional plan/progress files may remain untracked or modified.

- [x] **Step 6: Perform a manual Skill workflow review**

Verify against the approved design:

1. “查询最近 10 个订单” checks MCP readiness then chooses `tvcmall_list_orders`.
2. Missing MCP leads to the setup reference and no server clone.
3. Missing Key leads to `https://www.tvcmall.com/user/agentkeys` and pauses.
4. Existing Key is entered through `getpass`, not chat or command arguments.
5. Product ambiguity, placed-order shipping, shipped-order batch tracking, points, and balance use the documented tools.
6. Every error path preserves read-only and non-disclosure boundaries.

Expected: every scenario has one deterministic safe path with no contradiction between `SKILL.md`, references, README, and tests.

- [x] **Step 7: Commit verification fixes if any**

If verification required changes:

```powershell
git add .agents/skills/query-tvcmall-customer-data README.md tests .gitignore AGENTS.md
git commit -m "test: harden TVCMall skill verification"
```

If no changes were required, do not create an empty commit.

### Task 7: Final integration decision

**Files:**
- Modify: `docs/superpowers/plans/2026-08-12-tvcmall-customer-skill.md`

- [x] **Step 1: Mark every completed plan checkbox**

Update this plan so each executed step uses `- [x]`. Record any intentional deviation next to the affected step.

- [x] **Step 2: Run final evidence commands**

Run:

```powershell
python -m unittest discover -s tests -v
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\query-tvcmall-customer-data
git diff --check
git status --short --branch
git log --oneline --decorate -8
```

Expected: tests and Skill validation pass; Git output shows the planned commits and no unintended files.

- [x] **Step 3: Commit the completed implementation plan record**

```powershell
git add docs/superpowers/plans/2026-08-12-tvcmall-customer-skill.md
git commit -m "docs: complete TVCMall skill implementation plan"
```

- [x] **Step 4: Use the branch-finishing workflow**

Invoke `superpowers:finishing-a-development-branch` and present the supported integration choices. Do not push unless the user explicitly selects a push/PR option.
