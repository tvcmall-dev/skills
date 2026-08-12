from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tomllib
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
