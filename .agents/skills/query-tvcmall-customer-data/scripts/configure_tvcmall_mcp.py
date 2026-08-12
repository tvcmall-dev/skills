from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
import getpass
import os
from pathlib import Path
import re
import shutil
import tempfile
import tomllib
import sys


MCP_URL = "https://mcpserver.tvc-mall.com"
API_KEY_PATTERN = re.compile(r"^tmcp_v1_[^\s.]+\.[^\s.]+$")
TABLE_HEADER_PATTERN = re.compile(r"(?m)^\s*\[([^\]\r\n]+)\]\s*(?:#.*)?$")


@dataclass(frozen=True)
class ConfigureResult:
    config_path: Path
    backup_path: Path | None
    changed: bool


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

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{config_path.name}.", suffix=".tmp", dir=config_path.parent
    )
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


def resolve_config_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home) if codex_home else Path.home() / ".codex") / "config.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure the TVCMall remote MCP for Codex")
    parser.add_argument("--config", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm plaintext storage without an interactive yes/no prompt",
    )
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
