# TVCMall MCP Setup

## Determine Configuration State

1. Check whether the current session has the `tvcmall` MCP dependency and its expected tools.
2. If it does, call `tvcmall_auth_status` first; do not reinstall automatically.
3. If it does not, explain that installation follows the connection method documented by [TVCMall MCP](https://github.com/tvcmall-dev/mcp) and registers the remote MCP connection in the user's Codex configuration. Do not clone, build, or start the server repository.

## API Key

- Product and shipping queries can start without a personal `TVCMALL_API_KEY`; configure the default `tmcp_catalog.read` header value so the server can authorize default `catalog.read` access.
- Only after a catalog query returns `401` or `AUTH_REQUIRED`, direct the user to https://www.tvcmall.com/user/agentkeys to sign in and apply for a personal Key.
- Account tools for orders, tracking, points, and balance require a personal `TVCMALL_API_KEY`; direct the user to https://www.tvcmall.com/user/agentkeys before calling those tools if only `tmcp_catalog.read` is configured.
- Do not ask the user to paste the Key into chat.
- If the user has already sent a Key in chat, do not repeat it or continue using that value. Explain that it has been exposed, direct the user to revoke it immediately and request a new Key, then configure the new Key only through the system-terminal prompt with input echo disabled.
- Explain that the user has chosen to store the header value in plaintext in the user-level Codex `config.toml`.
- Accept either the default `tmcp_catalog.read` value or a complete personal PAT in the form `tmcp_v1_{tokenId}.{secret}`; do not add a `Bearer ` prefix.

## Configure

After receiving the user's explicit confirmation, run the interactive script in a visible operating-system terminal. Do not use an Agent client's embedded PTY for confirmation or Key input.

Resolve the script's absolute path from the Skill directory. On Windows, launch a visible PowerShell window with this non-secret command:

```powershell
$skillScript = (Resolve-Path 'scripts\configure_tvcmall_mcp.py').Path
Start-Process -FilePath 'powershell.exe' -ArgumentList @(
    '-NoProfile',
    '-Command',
    "python '$skillScript'; Write-Host ''; Read-Host 'Press Enter to close this window'"
) -WindowStyle Normal -Wait
```

Do not pass the Key as a command-line argument or environment variable. The user must enter it only at the script's hidden `TVCMALL_API_KEY` prompt in the system terminal. If the user presses Enter without entering a personal Key, the script writes the default catalog header:

```toml
[mcp_servers.tvcmall]
url = "https://openai.tvc-mall.com/mcp"
http_headers = { "TVCMALL_API_KEY" = "tmcp_catalog.read" }
```

When the user enters a personal PAT, the script writes that PAT as the `TVCMALL_API_KEY` value. The `/mcp` path is part of the endpoint: do not remove it or append it a second time. The script preserves other Codex settings and MCP Servers, refuses to overwrite invalid TOML, and creates a backup before replacing an existing valid configuration. Do not let another process edit the same `config.toml` while the script is running. The script detects changes made before replacement and fails safely, but the file replacement itself does not provide a cross-process lock.

On macOS or Linux, use a visible native terminal when a reliable launcher is available. If it is not, provide the exact non-secret command with the resolved script path and ask the user to open a system terminal manually. Do not fall back to an embedded client PTY, and never ask for the Key in chat.

After the system terminal closes, verify only non-sensitive state: the configuration modification time, backup existence, valid TOML, canonical endpoint, header presence, and whether the value has the expected default or personal-PAT shape. Do not print, hash, partially mask, or otherwise expose the configured value.

## Restart and Verify

Ask the user to restart Codex or start a new session. After confirming that the `tvcmall` tools are visible, call `tvcmall_auth_status`. `configured: true` only means that the current MCP session loaded a header value; verify the relevant permission through the read-only business query requested by the user.

## Configuration Errors

- Invalid TOML or a write failure: preserve the original configuration and report only the non-sensitive error and backup path.
- If the system terminal cannot be launched, explain the failure and provide the exact non-secret command for the user to run in a system terminal; do not use an embedded PTY as a fallback.
- If the user closes the system terminal before configuration completes, report that completion was not verified and offer to launch it again.
- Network errors or `5xx`: keep the canonical HTTPS configuration, explain that the service may be temporarily unavailable, and suggest trying again later.
- Do not fall back to HTTP, switch to the former endpoint, remove `/mcp`, or append a second `/mcp`.
