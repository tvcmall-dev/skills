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
LAUNCHER = ROOT / ".agents/skills/query-tvcmall-customer-data/scripts/launch_tvcmall_mcp_windows.cmd"
FAKE_KEY = "tmcp_v1_demo.secret"
CANCEL_EXIT_CODE = 1223


@unittest.skipUnless(os.name == "nt", "Windows PowerShell behavior")
class WindowsConfigurerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.powershell = shutil.which("powershell.exe")
        cls.codex = shutil.which("codex.exe") or shutil.which("codex.cmd") or shutil.which("codex")
        if not cls.powershell:
            raise unittest.SkipTest("Windows PowerShell is unavailable")
        candidates = [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "PowerShell/7/pwsh.exe",
            Path(os.environ.get("PROGRAMW6432", r"C:\Program Files")) / "PowerShell/7/pwsh.exe",
            Path(os.environ.get("USERPROFILE", str(Path.home())))
            / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe",
        ]
        cls.preferred_pwsh = next((candidate for candidate in candidates if candidate.is_file()), None)

    def run_case(self, case: str, temp_root: Path) -> subprocess.CompletedProcess[str]:
        if not self.codex:
            self.skipTest("The Codex command is unavailable")
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

    def assert_launcher_shows_dialog(
        self,
        environment: dict[str, str],
        expected_host: str | Path,
        working_directory: Path = ROOT,
    ) -> None:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        def matching_windows() -> dict[int, int]:
            matches: dict[int, int] = {}

            def inspect_window(handle: int, _parameter: int) -> bool:
                if not user32.IsWindowVisible(handle):
                    return True
                length = user32.GetWindowTextLengthW(handle)
                title = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(handle, title, len(title))
                if title.value == "Configure TVCMall MCP":
                    process_id = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(handle, ctypes.byref(process_id))
                    matches[handle] = process_id.value
                return True

            user32.EnumWindows(callback_type(inspect_window), 0)
            return matches

        def process_path(process_id: int) -> Path:
            process_handle = kernel32.OpenProcess(0x1000, False, process_id)
            self.assertTrue(process_handle, f"Could not inspect dialog process {process_id}")
            try:
                size = wintypes.DWORD(32768)
                buffer = ctypes.create_unicode_buffer(size.value)
                succeeded = kernel32.QueryFullProcessImageNameW(
                    process_handle,
                    0,
                    buffer,
                    ctypes.byref(size),
                )
                self.assertTrue(succeeded, f"Could not resolve dialog process {process_id}")
                return Path(buffer.value)
            finally:
                kernel32.CloseHandle(process_handle)

        existing_handles = set(matching_windows())
        command_processor = os.environ.get("COMSPEC", "cmd.exe")
        process = subprocess.Popen(
            [command_processor, "/d", "/c", str(LAUNCHER)],
            cwd=working_directory,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        window_handle = None
        owner_process_id = None
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and process.poll() is None:
                candidates = {
                    handle: process_id
                    for handle, process_id in matching_windows().items()
                    if handle not in existing_handles
                }
                if candidates:
                    window_handle, owner_process_id = next(iter(candidates.items()))
                    break
                time.sleep(0.1)

            if window_handle is None:
                output = process.stdout.read() if process.poll() is not None and process.stdout else ""
                self.fail(f"The native launcher did not show the masked dialog. {output}")

            self.assertEqual(
                os.path.normcase(process_path(owner_process_id)),
                os.path.normcase(Path(expected_host)),
            )
            user32.PostMessageW(window_handle, 0x0010, 0, 0)  # WM_CLOSE
            self.assertEqual(process.wait(timeout=10), CANCEL_EXIT_CODE)
        finally:
            if window_handle is not None and user32.IsWindow(window_handle):
                user32.PostMessageW(window_handle, 0x0010, 0, 0)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
            if process.stdout is not None:
                process.stdout.close()

    def test_native_launcher_prefers_powershell_7(self) -> None:
        if self.preferred_pwsh is None:
            self.skipTest("A fixed-location PowerShell 7 candidate is unavailable")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.toml"
            original = b'model = "gpt-5"\r\n'
            config_path.write_bytes(original)
            environment = os.environ.copy()
            environment["CODEX_HOME"] = directory
            self.assert_launcher_shows_dialog(environment, self.preferred_pwsh)
            self.assertEqual(config_path.read_bytes(), original)
            self.assertFalse(config_path.with_name("config.toml.bak").exists())

    def test_native_launcher_falls_back_without_python(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_home = root / "codex-home"
            codex_home.mkdir()
            config_path = codex_home / "config.toml"
            original = b'model = "gpt-5"\r\n'
            config_path.write_bytes(original)
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(codex_home)
            environment["USERPROFILE"] = str(root / "no-user-profile")
            environment["PROGRAMFILES"] = str(root / "no-program-files")
            environment["PROGRAMW6432"] = str(root / "no-program-w6432")
            system_root = Path(self.powershell).parents[3]
            environment["PATH"] = os.pathsep.join(
                [
                    str(Path(self.powershell).parent),
                    str(system_root / "System32"),
                    str(system_root),
                ]
            )
            self.assert_launcher_shows_dialog(environment, self.powershell)
            self.assertEqual(config_path.read_bytes(), original)
            self.assertFalse(config_path.with_name("config.toml.bak").exists())

    def test_pre_dialog_startup_failure_is_not_reported_as_cancel(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.toml"
            original = b'model = "gpt-5"\r\n'
            config_path.write_bytes(original)
            environment = os.environ.copy()
            environment["CODEX_HOME"] = directory
            escaped_script = str(SCRIPT).replace("'", "''")
            command = (
                "$ExecutionContext.SessionState.LanguageMode = 'ConstrainedLanguage'; "
                f"& '{escaped_script}'; exit $LASTEXITCODE"
            )
            completed = subprocess.run(
                [self.powershell, "-NoProfile", "-STA", "-Command", command],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )

            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            self.assertEqual(config_path.read_bytes(), original)
            self.assertFalse(config_path.with_name("config.toml.bak").exists())

    def test_native_launcher_ignores_untrusted_pwsh_on_the_caller_path(self) -> None:
        if self.preferred_pwsh is None:
            self.skipTest("A fixed-location PowerShell 7 candidate is unavailable")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy2(os.environ.get("COMSPEC", "cmd.exe"), root / "pwsh.exe")
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(root / "codex-home")
            environment["PATH"] = str(root) + os.pathsep + environment["PATH"]
            self.assert_launcher_shows_dialog(environment, self.preferred_pwsh, root)

    def test_native_launcher_tries_later_candidate_after_probe_failure(self) -> None:
        bundled_pwsh = (
            Path(os.environ.get("USERPROFILE", str(Path.home())))
            / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe"
        )
        if not bundled_pwsh.is_file():
            self.skipTest("The fixed-location bundled PowerShell runtime is unavailable")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            broken_install_root = root / "broken-install"
            broken_pwsh = broken_install_root / "PowerShell/7/pwsh.exe"
            broken_pwsh.parent.mkdir(parents=True)
            shutil.copy2(os.environ.get("COMSPEC", "cmd.exe"), broken_pwsh)
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(root / "codex-home")
            environment["PROGRAMFILES"] = str(broken_install_root)
            environment["PROGRAMW6432"] = str(broken_install_root)
            self.assert_launcher_shows_dialog(environment, bundled_pwsh)

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
                self.assertEqual(process.wait(timeout=5), CANCEL_EXIT_CODE)
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
