from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests/test_configure_tvcmall_mcp_windows.ps1"
SCRIPT = ROOT / ".agents/skills/query-tvcmall-customer-data/scripts/configure_tvcmall_mcp_windows.ps1"
FAKE_KEY = "tmcp_v1_demo.secret"


@unittest.skipUnless(os.name == "nt", "Windows PowerShell behavior")
class WindowsConfigurerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.powershell = shutil.which("powershell.exe")
        cls.codex = shutil.which("codex.exe") or shutil.which("codex.cmd") or shutil.which("codex")
        if not cls.powershell:
            raise unittest.SkipTest("Windows PowerShell is unavailable")
        if not cls.codex:
            raise unittest.SkipTest("The Codex command is unavailable")

    def run_case(self, case: str, temp_root: Path) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [
                self.powershell,
                "-NoProfile",
                "-STA",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(RUNNER),
                "-Case",
                case,
                "-TempRoot",
                str(temp_root),
                "-CodexExecutable",
                self.codex,
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        combined = completed.stdout + completed.stderr
        self.assertNotIn(FAKE_KEY, combined)
        self.assertEqual(completed.returncode, 0, combined)
        return completed

    def test_api_key_normalization_and_dialog_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.run_case("dialog", Path(directory))

    def test_hidden_console_launch_still_shows_dialog_and_cancel_is_safe(self) -> None:
        import ctypes
        from ctypes import wintypes

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = subprocess.SW_HIDE
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(root)
            process = subprocess.Popen(
                [self.powershell, "-NoProfile", "-STA", "-File", str(SCRIPT)],
                cwd=ROOT,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startup,
            )

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            window_handle = None

            def find_window(handle: int, _parameter: int) -> bool:
                nonlocal window_handle
                process_id = wintypes.DWORD()
                user32.GetWindowThreadProcessId(handle, ctypes.byref(process_id))
                if process_id.value != process.pid or not user32.IsWindowVisible(handle):
                    return True
                length = user32.GetWindowTextLengthW(handle)
                title = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(handle, title, len(title))
                if title.value == "Configure TVCMall MCP":
                    window_handle = handle
                    return False
                return True

            try:
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline and process.poll() is None:
                    user32.EnumWindows(callback_type(find_window), 0)
                    if window_handle is not None:
                        break
                    time.sleep(0.1)

                self.assertIsNotNone(window_handle, "The masked dialog never became visible")
                user32.PostMessageW(window_handle, 0x0010, 0, 0)  # WM_CLOSE
                self.assertEqual(process.wait(timeout=5), 1)
                self.assertFalse((root / "config.toml").exists())
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)

    def test_new_config_contains_only_the_canonical_tvcmall_server(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.run_case("new-config", root)
            parsed = tomllib.loads((root / "new/config.toml").read_text(encoding="utf-8"))
            tvcmall = parsed["mcp_servers"]["tvcmall"]
            self.assertEqual(tvcmall["url"], "https://openai.tvc-mall.com/mcp")
            self.assertEqual(tvcmall["http_headers"]["TVCMALL_API_KEY"], FAKE_KEY)

    def test_update_preserves_unrelated_toml_and_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.run_case("preserve-config", root)
            path = root / "preserve/config.toml"
            parsed = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["model"], "gpt-5")
            self.assertIn("[mcp_servers.tvcmall]", parsed["message"])
            self.assertEqual(parsed["custom_profiles"], [{"name": "first"}, {"name": "second"}])
            self.assertEqual(parsed["mcp_servers"]["other"]["url"], "https://example.com/mcp")
            self.assertEqual(parsed["mcp_servers"]["tvcmall"]["url"], "https://openai.tvc-mall.com/mcp")
            self.assertNotIn("OLD", parsed["mcp_servers"]["tvcmall"]["http_headers"])
            self.assertTrue(path.with_name("config.toml.bak").exists())

    def test_invalid_toml_is_not_modified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.run_case("invalid-config", root)
            path = root / "invalid/config.toml"
            self.assertEqual(path.read_text(encoding="utf-8"), "[broken")
            self.assertFalse(path.with_name("config.toml.bak").exists())

    def test_repeated_update_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.run_case("idempotent", root)
            path = root / "idempotent/config.toml"
            parsed = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["mcp_servers"]["tvcmall"]["http_headers"]["TVCMALL_API_KEY"], FAKE_KEY)


if __name__ == "__main__":
    unittest.main()
