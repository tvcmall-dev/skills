from __future__ import annotations

import re
import tomllib


MCP_URL = "https://mcpserver.tvc-mall.com"
API_KEY_PATTERN = re.compile(r"^tmcp_v1_[^\s.]+\.[^\s.]+$")
TABLE_HEADER_PATTERN = re.compile(r"(?m)^\s*\[([^\]\r\n]+)\]\s*(?:#.*)?$")


def validate_api_key(value: str) -> str:
    if value != value.strip() or not API_KEY_PATTERN.fullmatch(value):
        raise ValueError("TVCMALL_API_KEY must match tmcp_v1_{tokenId}.{secret} without Bearer")
    return value


def toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\b", "\\b").replace("\t", "\\t")
    escaped = escaped.replace("\n", "\\n").replace("\f", "\\f").replace("\r", "\\r")
    return f'"{escaped}"'


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
        f'http_headers = {{ "TVCMALL_API_KEY" = {toml_string(api_key)} }}{newline}'
    )
    updated = f"{base}{newline}{newline}{section}" if base else section
    tomllib.loads(updated)
    return updated
