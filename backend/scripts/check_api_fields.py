#!/usr/bin/env python3
"""
Fetch JSON API records and verify configured field values.

Usage:
    python scripts/check_api_fields.py checks.json

Config examples:
[
  {
    "url": "http://localhost:8000/health",
    "fields": [
      {"field": "status", "value": "ok"}
    ]
  },
  {
    "url": "http://localhost:8000/data/example",
    "field_values": {
      "type": "HumanMadeObject",
      "identified_by[0].content": "Example title"
    }
  }
]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class FieldCheck:
    field: str
    expected: Any


@dataclass(frozen=True)
class UrlCheck:
    url: str
    fields: list[FieldCheck]


@dataclass(frozen=True)
class CheckResult:
    url: str
    field: str
    expected: Any
    actual: Any = None
    passed: bool = False
    error: str | None = None


class ConfigError(ValueError):
    pass


def load_config(path: Path) -> list[UrlCheck]:
    try:
        raw_config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc

    checks = raw_config.get("checks") if isinstance(raw_config, dict) else raw_config
    if not isinstance(checks, list):
        raise ConfigError("Config must be a list of checks or an object with a 'checks' list")

    return [_parse_url_check(item, index) for index, item in enumerate(checks, 1)]


def _parse_url_check(item: Any, index: int) -> UrlCheck:
    if not isinstance(item, dict):
        raise ConfigError(f"Check #{index} must be an object")

    url = item.get("url")
    if not isinstance(url, str) or not url:
        raise ConfigError(f"Check #{index} must include a non-empty 'url'")

    field_checks: list[FieldCheck] = []

    if "field" in item or "value" in item:
        if "field" not in item or "value" not in item:
            raise ConfigError(f"Check #{index} must include both 'field' and 'value'")
        field_checks.append(FieldCheck(str(item["field"]), item["value"]))

    fields = item.get("fields")
    if fields is not None:
        if not isinstance(fields, list):
            raise ConfigError(f"Check #{index} 'fields' must be a list")
        for field_index, field_item in enumerate(fields, 1):
            if not isinstance(field_item, dict):
                raise ConfigError(f"Check #{index} field #{field_index} must be an object")
            if "field" not in field_item or "value" not in field_item:
                raise ConfigError(
                    f"Check #{index} field #{field_index} must include 'field' and 'value'"
                )
            field_checks.append(FieldCheck(str(field_item["field"]), field_item["value"]))

    field_values = item.get("field_values")
    if field_values is not None:
        if not isinstance(field_values, dict):
            raise ConfigError(f"Check #{index} 'field_values' must be an object")
        for field, expected in field_values.items():
            field_checks.append(FieldCheck(str(field), expected))

    if not field_checks:
        raise ConfigError(
            f"Check #{index} must include 'field'/'value', 'fields', or 'field_values'"
        )

    return UrlCheck(url=url, fields=field_checks)


def fetch_json(url: str, timeout: float) -> Any:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "nlux-api-checker"})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset)
    return json.loads(body)


def get_field(document: Any, field_path: str) -> Any:
    current = document
    for token in _field_tokens(field_path):
        if isinstance(token, int):
            if not isinstance(current, list):
                raise KeyError(f"expected list before index [{token}]")
            current = current[token]
        else:
            if not isinstance(current, dict):
                raise KeyError(f"expected object before field '{token}'")
            current = current[token]
    return current


def _field_tokens(field_path: str) -> list[str | int]:
    if not field_path:
        raise KeyError("empty field path")

    if field_path.startswith("/"):
        return [_json_pointer_token(part) for part in field_path.split("/")[1:]]

    tokens: list[str | int] = []
    for part in field_path.split("."):
        if not part:
            raise KeyError(f"invalid field path '{field_path}'")
        name, indexes = _split_indexes(part)
        if name:
            tokens.append(name)
        tokens.extend(indexes)
    return tokens


def _json_pointer_token(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _split_indexes(part: str) -> tuple[str, list[int]]:
    name = part.split("[", 1)[0]
    indexes: list[int] = []
    remainder = part[len(name):]

    while remainder:
        if not remainder.startswith("["):
            raise KeyError(f"invalid field segment '{part}'")
        close = remainder.find("]")
        if close == -1:
            raise KeyError(f"invalid field segment '{part}'")
        index_value = remainder[1:close]
        if not index_value.isdigit():
            raise KeyError(f"invalid list index '{index_value}'")
        indexes.append(int(index_value))
        remainder = remainder[close + 1:]

    return name, indexes


def run_checks(checks: list[UrlCheck], timeout: float) -> list[CheckResult]:
    results: list[CheckResult] = []

    for check in checks:
        try:
            document = fetch_json(check.url, timeout)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            results.extend(
                CheckResult(
                    url=check.url,
                    field=field_check.field,
                    expected=field_check.expected,
                    error=f"fetch failed: {exc}",
                )
                for field_check in check.fields
            )
            continue

        for field_check in check.fields:
            try:
                actual = get_field(document, field_check.field)
                results.append(
                    CheckResult(
                        url=check.url,
                        field=field_check.field,
                        expected=field_check.expected,
                        actual=actual,
                        passed=actual == field_check.expected,
                    )
                )
            except (KeyError, IndexError) as exc:
                results.append(
                    CheckResult(
                        url=check.url,
                        field=field_check.field,
                        expected=field_check.expected,
                        error=f"field not found: {exc}",
                    )
                )

    return results


def print_results(results: list[CheckResult]) -> None:
    for result in results:
        if result.passed:
            print(f"PASS {result.url} {result.field} == {json.dumps(result.expected)}")
        elif result.error:
            print(f"FAIL {result.url} {result.field}: {result.error}")
        else:
            print(
                "FAIL "
                f"{result.url} {result.field}: "
                f"expected {json.dumps(result.expected)}, got {json.dumps(result.actual)}"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to the JSON checks config")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
    args = parser.parse_args(argv)

    try:
        checks = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    results = run_checks(checks, args.timeout)
    print_results(results)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
