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


MCP_URL = "https://openapi.tvc-mall.com/mcp"
API_KEY_PATTERN = re.compile(r"^tmcp_v1_[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")


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
    escapes = {
        "\b": "\\b",
        "\t": "\\t",
        "\n": "\\n",
        "\f": "\\f",
        "\r": "\\r",
        '"': '\\"',
        "\\": "\\\\",
    }
    escaped = "".join(
        escapes.get(character, f"\\u{ord(character):04X}" if ord(character) < 0x20 or ord(character) == 0x7F else character)
        for character in value
    )
    return f'"{escaped}"'


def _marker_path(value: object, marker: str, path: tuple[str, ...] = ()) -> tuple[str, ...] | None:
    if isinstance(value, dict):
        if value.get(marker) is True:
            return path
        for key, child in value.items():
            found = _marker_path(child, marker, (*path, key))
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _marker_path(child, marker, path)
            if found is not None:
                return found
    return None


def _table_headers(source: str) -> list[tuple[int, tuple[str, ...]]]:
    marker = "__tvcmall_config_table_marker__"
    while marker in source:
        marker += "_"
    newline = "\r\n" if "\r\n" in source else "\n"
    headers: list[tuple[int, tuple[str, ...]]] = []
    offset = 0

    for line in source.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if body.lstrip(" \t").startswith("["):
            assignment = f"{marker} = true"
            try:
                isolated = tomllib.loads(f"{body}\n{assignment}\n")
                isolated_path = _marker_path(isolated, marker)
            except tomllib.TOMLDecodeError:
                isolated_path = None

            if isolated_path is not None:
                body_end = offset + len(body)
                injected = f"{source[:body_end]}{newline}{assignment}{source[body_end:]}"
                try:
                    contextual = tomllib.loads(injected)
                    contextual_path = _marker_path(contextual, marker)
                except tomllib.TOMLDecodeError:
                    contextual_path = None
                if contextual_path == isolated_path:
                    headers.append((offset, isolated_path))
        offset += len(line)

    return headers


def _remove_tvcmall_tables(source: str) -> str:
    headers = _table_headers(source)
    ranges: list[tuple[int, int]] = []
    for index, (start, path) in enumerate(headers):
        if path[:2] == ("mcp_servers", "tvcmall"):
            end = headers[index + 1][0] if index + 1 < len(headers) else len(source)
            ranges.append((start, end))
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
    existed = config_path.exists()
    source = _read_config_text(config_path) if existed else ""
    updated = upsert_tvcmall_config(source, api_key)
    if updated == source:
        return ConfigureResult(config_path, None, False)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path: Path | None = None
    if config_path.exists():
        backup_path = config_path.with_name(f"{config_path.name}.bak")
        shutil.copy2(config_path, backup_path)

    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{config_path.name}.", suffix=".tmp", dir=config_path.parent
        )
    except OSError as exc:
        exc.backup_path = backup_path
        raise
    temporary_path = Path(temporary_name)
    try:
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
                stream.write(updated)
                stream.flush()
                os.fsync(stream.fileno())
            if config_path.exists() != existed or (existed and _read_config_text(config_path) != source):
                raise RuntimeError("Codex config changed during update; no changes were applied")
            os.replace(temporary_path, config_path)
        except OSError as exc:
            exc.backup_path = backup_path
            raise
    finally:
        temporary_path.unlink(missing_ok=True)
    return ConfigureResult(config_path, backup_path, True)


def _read_config_text(config_path: Path) -> str:
    with config_path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


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
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Configuration failed: {exc}", file=sys.stderr)
        backup_path = getattr(exc, "backup_path", None)
        if backup_path:
            print(f"Backup available: {backup_path}", file=sys.stderr)
        return 2

    state = "updated" if result.changed else "already current"
    print(f"TVCMall MCP configuration {state}: {result.config_path}")
    if result.backup_path:
        print(f"Backup created: {result.backup_path}")
    print("Restart Codex or start a new session, then verify the tvcmall MCP tools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
