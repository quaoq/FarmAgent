"""
Custom decorator emulating OpenAI tool definition (`@function_tool` decorator)
(https://openai.github.io/openai-agents-python/tools/#function-tools)
to expand for ARE CORE evaluation aspects (READ, WRITE, etc.)
"""

from typing import Callable, Union
from agents import Agent, FunctionTool, function_tool

def prune_self_from_schema(schema: dict) -> dict:
    schema = schema.copy()
    schema["properties"] = {
        k: v for k, v in schema.get("properties", {}).items() if k != "self"
    }
    if "required" in schema:
        schema["required"] = [k for k in schema["required"] if k != "self"]
    return schema


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


def build_tool_schema(func: Callable) -> dict:

    agent = Agent(
        name="Assistant",
        tools=[function_tool(func)],
    )
    tool = agent.tools[0]
    assert isinstance(tool, FunctionTool)
    schema = prune_self_from_schema(tool.params_json_schema)
    # schema = tool.params_json_schema

    # Build the final tool schema dictionary.
    tool_dict = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": schema,
        }
    }
    # print(json.dumps(tool_dict, indent=2))
    return tool_dict


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
