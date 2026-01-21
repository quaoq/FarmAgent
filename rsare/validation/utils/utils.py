from rsare.validation.utils.data_structures import (
    ToolInfo,
    FunctionCall,
    FunctionArgument,
)


def symbol_generator():
    """Yields symbols: 'A', 'B', ..., 'Z', 'AA', 'AB', ... skipping 'X'"""
    i = 0
    while True:
        s = ""
        n = i
        while True:
            s = chr(ord("A") + (n % 26)) + s
            if s == "X":
                s = chr(ord("A") + ((n + 1) % 26)) + s[1:]  # skip 'X'
            n = n // 26 - 1
            if n < 0:
                break
        yield s
        i += 1


def extract_tool_names(tools: list[dict]) -> list[ToolInfo]:
    """
    Extract ToolInfo objects from OpenAI-style tool schemas.

    `tools` is expected to be a list of dicts like:
        {
            "type": "function",
            "function": {
                "name": "<AppClass__tool_name>" or "<tool_name>",
                "description": "...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg1": {"type": "string", ...},
                        ...
                    },
                    ...
                },
            }
        }

    This function:
    - strips any app class prefix before "__" from the function name
    - collects argument names and their JSON-schema `"type"` as strings
    """
    tool_infos = list()
    for tool in tools:
        # Defensive access to the inner "function" dict
        func_def = tool.get("function", {})
        full_name = func_def.get("name", "")

        # Remove app class name prefix (e.g., "ConfigurationsApp__set_config" -> "set_config")
        if "__" in full_name:
            clean_name = full_name.split("__", 1)[1]  # Take everything after first "__"
        else:
            clean_name = full_name

        # Build arguments dict from JSON-schema "properties"
        params = func_def.get("parameters", {}) or {}
        properties = params.get("properties", {}) or {}
        arguments: dict[str, str] = {}
        for arg_name, arg_schema in properties.items():
            # Use JSON schema "type" as our simple textual type; default to "any"
            arg_type = arg_schema.get("type", "any")
            arguments[arg_name] = arg_type

        tool_info = ToolInfo(
            name=clean_name,
            arguments=arguments,
        )
        tool_infos.append(tool_info)
    return tool_infos

def parse_agent_output(
    agent_workflow_dag, tool_infos: list[ToolInfo]
) -> list[FunctionCall]:
    """
    Convert an agent workflow DAG (e.g. `engine.agent.workflow.dag`)
    into a linear list of `FunctionCall` objects.

    Args:
        agent_workflow_dag: Typically `engine.agent.workflow.dag`, a dict
            mapping step names -> WorkflowStep. Each `WorkflowStep` is
            expected to have `tool_name` and `tool_args` attributes.
        tool_infos: List of `ToolInfo` describing the valid tools. Steps
            whose `tool_name` is not in this list are ignored.
    """
    agent_sequence: list[FunctionCall] = []

    # Precompute allowed tool names for quick membership checks
    allowed_tool_names = {info.name for info in tool_infos}

    # If a dict is passed (the DAG), iterate over its values
    steps = (
        agent_workflow_dag.values()
        if isinstance(agent_workflow_dag, dict)
        else agent_workflow_dag
    )

    for step in steps:
        # WorkflowStep.tool_name is the function name to call
        function_name = getattr(step, "tool_name", None)
        if not function_name:
            continue

        # Skip if this function is not part of the known tools
        if function_name not in allowed_tool_names:
            continue

        # Extract arguments from WorkflowStep.tool_args, excluding 'self'
        raw_args = getattr(step, "tool_args", {}) or {}
        arguments: dict[str, FunctionArgument] = {}
        for arg_name, arg_value in raw_args.items():
            if arg_name == "self":
                continue
            arguments[arg_name] = FunctionArgument(
                name=arg_name,
                value=arg_value,
                excluded_values=None,
                type=type(arg_value).__name__ if arg_value is not None else "NoneType",
            )

        function_call = FunctionCall(name=function_name, arguments=arguments)
        agent_sequence.append(function_call)

    return agent_sequence
def fc2symbol(func_call: FunctionCall, alphabet: dict[str, FunctionCall]) -> str:
    """
    Convert function call to corresponding symbol in alphabet.

    Args:
        func_call: Function call to convert
        alphabet: Symbol to function call mapping

    Returns:
        Corresponding symbol
    """
    out_symbol = ""

    # keep only symbols that match the function name
    candidate_symbols = [
        symbol for symbol, fc in alphabet.items() if fc.name == func_call.name
    ]

    if len(candidate_symbols) == 1:
        return candidate_symbols[0]

    # check non-general matches
    for symbol in candidate_symbols:
        # non-general candidates have a 1-1 match of arguments
        check = all(
            str(func_call.arguments[arg_name].value)
            == str(alphabet[symbol].arguments[arg_name].value)
            for arg_name in func_call.arguments
        )
        if check:
            out_symbol = symbol
            break
        else:
            # this works because we are guaranteed only one general symbol per function
            # and that general symbols are last in the candidate_symbols list
            out_symbol = symbol

    return out_symbol