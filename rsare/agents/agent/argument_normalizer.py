from __future__ import annotations

import math
import re
from typing import Any


_INT_PATTERN = re.compile(r"^[+-]?\d+$")
_FLOAT_PATTERN = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")


def _extract_string_from_schema_dict(value: dict[str, Any]) -> str | None:
    description = value.get("description")
    if isinstance(description, str):
        return description

    content = value.get("content")
    if isinstance(content, dict):
        content_description = content.get("description")
        if isinstance(content_description, str):
            return content_description

    return None


def _coerce_to_integer(value: Any, *, argument_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(
            f"argument '{argument_name}' expected integer but got boolean '{value}'"
        )
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError(
            f"argument '{argument_name}' expected integer but got non-integer float '{value}'"
        )
    if isinstance(value, str):
        stripped = value.strip()
        if _INT_PATTERN.fullmatch(stripped):
            return int(stripped)
    raise ValueError(
        f"argument '{argument_name}' expected integer but got value of type {type(value).__name__}"
    )


def _coerce_to_number(value: Any, *, argument_name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(
            f"argument '{argument_name}' expected number but got boolean '{value}'"
        )
    if isinstance(value, (int, float)):
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric
        raise ValueError(
            f"argument '{argument_name}' expected finite number but got '{value}'"
        )
    if isinstance(value, str):
        stripped = value.strip()
        if _FLOAT_PATTERN.fullmatch(stripped):
            numeric = float(stripped)
            if math.isfinite(numeric):
                return numeric
    raise ValueError(
        f"argument '{argument_name}' expected number but got value of type {type(value).__name__}"
    )


def _coerce_to_boolean(value: Any, *, argument_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    raise ValueError(
        f"argument '{argument_name}' expected boolean but got value of type {type(value).__name__}"
    )


def _coerce_to_string(value: Any, *, argument_name: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        maybe_description = _extract_string_from_schema_dict(value)
        if maybe_description is not None:
            return maybe_description
    if isinstance(value, (int, float, bool)):
        return str(value)
    raise ValueError(
        f"argument '{argument_name}' expected string but got value of type {type(value).__name__}"
    )


def _coerce_value(value: Any, expected_type: str, *, argument_name: str) -> Any:
    if expected_type == "integer":
        return _coerce_to_integer(value, argument_name=argument_name)
    if expected_type == "number":
        return _coerce_to_number(value, argument_name=argument_name)
    if expected_type == "boolean":
        return _coerce_to_boolean(value, argument_name=argument_name)
    if expected_type == "string":
        return _coerce_to_string(value, argument_name=argument_name)
    return value


def normalize_tool_arguments(
    *,
    tool_name: str,
    raw_arguments: Any,
    schema_properties: dict[str, Any] | None,
) -> dict[str, Any]:
    if raw_arguments is None:
        return {}
    if not isinstance(raw_arguments, dict):
        raise ValueError(
            f"Tool '{tool_name}' expected object arguments, got {type(raw_arguments).__name__}"
        )

    if not schema_properties:
        return dict(raw_arguments)

    normalized: dict[str, Any] = {}
    for argument_name, value in raw_arguments.items():
        property_schema = schema_properties.get(argument_name, {})
        expected_type = property_schema.get("type")
        if isinstance(expected_type, list):
            expected_type = next(
                (item for item in expected_type if item != "null"),
                expected_type[0] if expected_type else None,
            )
        if not isinstance(expected_type, str):
            normalized[argument_name] = value
            continue
        normalized[argument_name] = _coerce_value(
            value,
            expected_type,
            argument_name=argument_name,
        )
    return normalized
