"""
Tool discovery and JSON-schema generation for RSARE apps.

This module intentionally avoids a hard dependency on `openai-agents`.
It generates OpenAI-compatible function schemas from Python signatures.
"""

from __future__ import annotations

import inspect
import types
import typing
from typing import Any, Callable, get_args, get_origin


def agent_tool(func=None, *, doc_enabled=True):
    def decorator(f):
        f.is_agent_tool = True
        if not (doc_enabled):
            f.__doc__ = ""  # Strips the docstring at runtime
        return f
    return decorator if func is None else decorator(func)


def agent_toolset(obj) -> list:
    """
    Returns a list with callable methods that are marked with
    the 'is_agent_tool' attribute on the given object.

    Args:
        obj: The object (typically an agent instance) to inspect.

    Returns:
        A list where items callable methods.
    """
    # FIX: accept either an instance or a class, and if it's a class, instantiate it once
    if isinstance(obj, type):   # it's a class
        obj = obj()             # instantiate once

    tools = []
    for attr_name in dir(obj):
        attr = getattr(obj, attr_name)
        if callable(attr) and getattr(attr, "is_agent_tool", False):
            tools.append(attr)
    return tools


def _annotation_to_json_schema(annotation: Any) -> dict[str, Any]:
    if annotation in (inspect.Signature.empty, Any):
        return {"type": "string"}
    if isinstance(annotation, str):
        normalized = annotation.strip().lower()
        if normalized in {"str", "string"}:
            return {"type": "string"}
        if normalized in {"int", "integer"}:
            return {"type": "integer"}
        if normalized in {"float", "number"}:
            return {"type": "number"}
        if normalized in {"bool", "boolean"}:
            return {"type": "boolean"}
        return {"type": "string"}

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is None:
        if annotation is str:
            return {"type": "string"}
        if annotation is int:
            return {"type": "integer"}
        if annotation is float:
            return {"type": "number"}
        if annotation is bool:
            return {"type": "boolean"}
        if annotation is dict:
            return {"type": "object"}
        if annotation in (list, tuple, set):
            return {"type": "array", "items": {"type": "string"}}
        return {"type": "string"}

    if origin in (list, tuple, set):
        item_type = args[0] if args else str
        return {"type": "array", "items": _annotation_to_json_schema(item_type)}

    if origin is dict:
        return {"type": "object"}

    if origin is type(None):
        return {"type": "null"}

    if origin in (typing.Union, types.UnionType):
        non_none_args = [arg for arg in args if arg is not type(None)]
        if not non_none_args:
            return {"type": "string"}
        return _annotation_to_json_schema(non_none_args[0])

    return {"type": "string"}


def build_tool_schema(func: Callable) -> dict:
    signature = inspect.signature(func)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, parameter in signature.parameters.items():
        if param_name in {"self", "cls"}:
            continue
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        properties[param_name] = _annotation_to_json_schema(parameter.annotation)
        if parameter.default is inspect.Parameter.empty:
            required.append(param_name)

    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        parameters_schema["required"] = required

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": inspect.getdoc(func) or "",
            "parameters": parameters_schema,
        },
    }


# Hacky wrapper to use OpenAI's robust tool schema creation
def build_toolset(toolsets):

    assert isinstance(toolsets, list)
    # Aggregate all tools from the provided toolset objects.
    tools = []
    tool_to_app_name = {}
    for toolset in toolsets:
        # extract_agent_toolset is a utility function that returns a dict of {tool_name: callable}
        toolset_list = agent_toolset(toolset)
        # Track which app each tool belongs to
        app_name = getattr(toolset, 'name', toolset.__class__.__name__)
        for tool in toolset_list:
            tool_to_app_name[tool] = app_name
        # We add the tool callables to our aggregated list.
        tools.extend(toolset_list)
    # turn python functions into tools and save a reverse map
    # following: https://cookbook.openai.com/examples/orchestrating_agents
    tool_schemas = []
    tools_map = {}
    for tool in tools:
        schema = build_tool_schema(tool)
        app_name = tool_to_app_name[tool]
        original_name = schema["function"]["name"]
        # Prefix tool name with app name to ensure uniqueness
        prefixed_name = f"{app_name}__{original_name}"
        schema["function"]["name"] = prefixed_name
        tool_schemas.append(schema)
        tools_map[prefixed_name] = tool

    return tools, tool_schemas, tools_map
