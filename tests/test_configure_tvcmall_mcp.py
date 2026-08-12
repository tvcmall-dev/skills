from __future__ import annotations

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest import mock


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

    def test_rejects_non_ascii_and_control_characters(self) -> None:
        for value in ("tmcp_v1_demo.secrét", "tmcp_v1_demo.sec\x00ret"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                configurer.validate_api_key(value)

    def test_toml_string_escapes_quotes_and_backslashes(self) -> None:
        self.assertEqual(configurer.toml_string('a"b\\c'), '"a\\"b\\\\c"')

    def test_toml_string_escapes_forbidden_control_characters(self) -> None:
        self.assertEqual(configurer.toml_string("a\x00\x7fb"), '"a\\u0000\\u007Fb"')


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

    def test_ignores_table_like_text_inside_multiline_strings(self) -> None:
        source = '''message = """
[mcp_servers.tvcmall]
This is documentation, not a TOML table.
"""

[mcp_servers.other]
url = "https://example.com/mcp"
'''
        updated = configurer.upsert_tvcmall_config(source, "tmcp_v1_demo.secret")
        parsed = tomllib.loads(updated)
        self.assertIn("[mcp_servers.tvcmall]", parsed["message"])
        self.assertEqual(parsed["mcp_servers"]["other"]["url"], "https://example.com/mcp")

    def test_preserves_array_table_after_tvcmall_section(self) -> None:
        source = '''[mcp_servers.tvcmall]
url = "https://old.invalid"

[[profiles]]
name = "first"

[[profiles]]
name = "second"
'''
        updated = configurer.upsert_tvcmall_config(source, "tmcp_v1_demo.secret")
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["profiles"], [{"name": "first"}, {"name": "second"}])

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


class FileUpdateTests(unittest.TestCase):
    def test_creates_backup_and_preserves_other_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            original = '[mcp_servers.other]\nurl = "https://example.com/mcp"\n'
            path.write_text(original, encoding="utf-8")
            result = configurer.configure_file(path, "tmcp_v1_demo.secret")
            self.assertTrue(result.changed)
            assert result.backup_path is not None
            self.assertEqual(result.backup_path.read_text(encoding="utf-8"), original)
            parsed = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertIn("other", parsed["mcp_servers"])
            self.assertIn("tvcmall", parsed["mcp_servers"])

    def test_file_update_preserves_crlf_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_bytes(b'model = "gpt-5"\r\n')
            configurer.configure_file(path, "tmcp_v1_demo.secret")
            updated = path.read_bytes()
            self.assertIn(b"\r\n", updated)
            self.assertNotIn(b"\n", updated.replace(b"\r\n", b""))

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

    def test_concurrent_change_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text('model = "original"\n', encoding="utf-8")

            def replace_source_during_write(_descriptor: int) -> None:
                path.write_text('model = "external"\n', encoding="utf-8")

            with mock.patch.object(configurer.os, "fsync", side_effect=replace_source_during_write):
                with self.assertRaisesRegex(RuntimeError, "changed during update"):
                    configurer.configure_file(path, "tmcp_v1_demo.secret")
            self.assertEqual(path.read_text(encoding="utf-8"), 'model = "external"\n')

    def test_read_only_destination_failure_keeps_original(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            original = 'model = "gpt-5"\n'
            path.write_text(original, encoding="utf-8")
            with mock.patch.object(configurer.tempfile, "mkstemp", side_effect=PermissionError("read only")):
                with self.assertRaises(PermissionError):
                    configurer.configure_file(path, "tmcp_v1_demo.secret")
            self.assertEqual(path.read_text(encoding="utf-8"), original)


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

    def test_main_reports_backup_path_when_replace_fails(self) -> None:
        secret = "tmcp_v1_fake.secret"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text('model = "gpt-5"\n', encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch.object(configurer.getpass, "getpass", return_value=secret):
                with mock.patch.object(configurer.os, "replace", side_effect=OSError("blocked")):
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        code = configurer.main(["--config", str(path), "--yes"])
            output = stdout.getvalue() + stderr.getvalue()
            self.assertEqual(code, 2)
            self.assertIn(str(path.with_name("config.toml.bak")), output)
            self.assertNotIn(secret, output)

    def test_main_reports_backup_path_when_temp_creation_fails(self) -> None:
        secret = "tmcp_v1_fake.secret"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text('model = "gpt-5"\n', encoding="utf-8")
            stderr = io.StringIO()
            with mock.patch.object(configurer.getpass, "getpass", return_value=secret):
                with mock.patch.object(configurer.tempfile, "mkstemp", side_effect=PermissionError("read only")):
                    with contextlib.redirect_stderr(stderr):
                        code = configurer.main(["--config", str(path), "--yes"])
            self.assertEqual(code, 2)
            self.assertIn(str(path.with_name("config.toml.bak")), stderr.getvalue())
            self.assertNotIn(secret, stderr.getvalue())
