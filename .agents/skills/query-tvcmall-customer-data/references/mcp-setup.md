# TVCMall MCP Setup

## Determine Configuration State

1. Check whether the current session has the `tvcmall` MCP dependency and its expected tools.
2. If it does, call `tvcmall_auth_status` first; do not reinstall automatically.
3. If it does not, explain that installation follows the connection method documented by [TVCMall MCP](https://github.com/tvcmall-dev/mcp) and registers the remote MCP connection in the user's Codex configuration. Do not clone, build, or start the server repository.

## API Key

- Ask whether the user already has a `TVCMALL_API_KEY`.
- If not, direct the user to https://www.tvcmall.com/user/agentkeys to sign in and apply, then pause configuration until the user has obtained a Key.
- Do not ask the user to paste the Key into chat.
- If the user has already sent a Key in chat, do not repeat it or continue using that value. Explain that it has been exposed, direct the user to revoke it immediately and request a new Key, then configure the new Key only through the native masked Windows dialog or, for the Python fallback, a hidden prompt in a visible operating-system terminal.
- Explain that the user has chosen to store the Key in plaintext in the user-level Codex `config.toml`.
- Accept only a complete personal PAT in the form `tmcp_v1_{tokenId}.{secret}`; do not add a `Bearer ` prefix.

## Configure

After receiving the user's explicit confirmation, resolve the selected script from the installed Skill directory and launch it by its absolute path. The Agent may run the non-secret launcher command, but the Key itself must never enter chat, an Agent client's embedded PTY, command-line arguments, environment variables, or piped input.

### Windows: Native Dialog

Use `scripts/launch_tvcmall_mcp_windows.cmd` by default. The launcher checks PowerShell 7.0 or later candidates only in the standard installation directory and the current user's Codex bundled-runtime location; it does not search the current project or arbitrary `PATH` entries. These are fixed-location assumptions, not executable signature verification. It uses the built-in Windows PowerShell 5.1 fallback when no eligible PowerShell 7 candidate is found. Both paths display the same local Windows Forms dialog, whose Key field is masked by default. The Windows path does not require or invoke Python. The launcher invokes the installed `scripts/configure_tvcmall_mcp_windows.ps1` with `-NoProfile`, `-STA`, `-ExecutionPolicy Bypass`, and `-File`. The process-scoped execution-policy option cannot override an organization-enforced Group Policy.

The dialog provides a dedicated Paste button, received-character feedback, an explicit Show/Hide control, inline validation with retry, and plaintext-storage confirmation. It uses the installed Codex command to validate and update a temporary copy before replacing the user configuration.

Resolve `<absolute-skill-directory>` before running this command; do not pass a relative launcher path. Execute the launcher directly and wait for its exit code:

```powershell
$skillLauncher = (Resolve-Path -LiteralPath '<absolute-skill-directory>\scripts\launch_tvcmall_mcp_windows.cmd').Path
& $skillLauncher
$setupExitCode = $LASTEXITCODE
```

Exit code `0` means configuration completed, `1223` means the user cancelled or closed the dialog, and `2` means a handled dialog startup failure. Any other nonzero result is also a launch or host failure; only `1223` may be classified as cancellation. Do not report success for a nonzero result.

Do not use `-WindowStyle Hidden` around this launcher or its PowerShell child. Windows PowerShell 5.1 can apply that startup state to the first GUI window, and a hidden console also conceals execution-policy or startup errors. Running the non-secret launcher command in an Agent shell is allowed. Do not use an Agent client's embedded PTY for Key entry; all Key entry must remain in the native dialog. Windows can still deny automatic keyboard focus; if the visible dialog is not focused, ask the user to click it. Do not pass the Key as a command-line argument or environment variable, and do not send it as piped input. The dialog trims surrounding copied whitespace, rejects empty or malformed values without changing the configuration, and keeps the dialog open for another attempt.

If automatic launch fails, do not ask for the Key in chat or fall back to Key entry in an Agent client's embedded PTY. Give the user the resolved absolute launcher path and ask them to run this non-secret command in a visible system PowerShell:

```powershell
& '<resolved-absolute-launcher-path>'
```

### Python Fallback

Use `scripts/configure_tvcmall_mcp.py` on macOS/Linux, or on Windows only when the native dialog cannot be used and Python 3.11 or later is already available. Run it in a visible operating-system terminal, never in an Agent client's embedded PTY. Because plaintext storage was already confirmed, invoke it with `--yes` and its resolved absolute path:

```text
python -X utf8 "<resolved-absolute-python-script-path>" --yes
```

Use `python3` where that is the platform's Python 3 command. If an automatic native-terminal launcher is unavailable, give the user the fully substituted non-secret command to run manually. Do not pass the Key in the command, an environment variable, or piped input. The fallback also trims surrounding copied whitespace and rejects malformed values without changing the configuration.

Both configuration paths produce:

```toml
[mcp_servers.tvcmall]
url = "https://openai.tvc-mall.com/mcp"
http_headers = { "TVCMALL_API_KEY" = "<TVCMALL_PAT>" }
```

`<TVCMALL_PAT>` is a placeholder only. The `/mcp` path is part of the endpoint: do not remove it or append it a second time. Both scripts preserve other Codex settings and MCP Servers, refuse to overwrite invalid TOML, and create `config.toml.bak` before replacing an existing valid configuration. A later changed update replaces that fixed backup so it contains the immediately previous configuration without accumulating credential copies. Do not let another process edit the same `config.toml` while setup is running. Both scripts compare the file immediately before replacement and stop if it has already changed, but there is still a small race window because the final replacement does not provide a cross-process lock.

After the dialog or fallback terminal closes, verify only non-sensitive state: the configuration modification time, backup existence, valid TOML, canonical endpoint, header presence, and whether the value has the expected personal-PAT shape. Do not print, hash, partially mask, or otherwise expose the configured value.

## Restart and Verify

Ask the user to restart Codex or start a new session. After confirming that the `tvcmall` tools are visible, call `tvcmall_auth_status`. `configured: true` only means that the current MCP session loaded a Key; verify the relevant permission through the read-only business query requested by the user.

## Configuration Errors

- Invalid TOML or a write failure: preserve the original configuration and report only the non-sensitive error and backup path.
- If automatic Windows launch fails, provide the exact non-secret command with the resolved absolute `.cmd` launcher path. The user may run it in a visible system PowerShell; never ask them to enter the Key in an Agent client's embedded PTY.
- If the native Windows script itself cannot run, use the Python fallback only when Python 3.11 or later is already available. Do not require Python for the normal Windows path.
- If the user cancels or closes the dialog or fallback terminal before configuration completes, report that completion was not verified and offer to launch it again.
- Network errors or `5xx`: keep the canonical HTTPS configuration, explain that the service may be temporarily unavailable, and suggest trying again later.
- Do not fall back to HTTP, switch to the former endpoint, remove `/mcp`, or append a second `/mcp`.
