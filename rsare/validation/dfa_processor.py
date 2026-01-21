"""
DFA processing and state machine logic.

This module handles DFA generation, alphabet creation,
and state transition analysis for validation.
"""

from copy import copy

from rsare.validation.utils.data_structures import FunctionCall, ToolInfo, FunctionArgument, Node, Transition
from rsare.validation.utils.utils import symbol_generator


def generate_alphabet(
    expected_sequence: list[FunctionCall], tools: list[ToolInfo]
) -> dict[str, FunctionCall]:
    """
    Generate alphabet mapping symbols to function calls.

    Args:
        expected_sequence: Expected sequence of function calls
        tools: Available tools/functions

    Returns:
        Dictionary mapping symbols to function calls
    """
    gen = symbol_generator()
    used_tools = {
        tool.name: [
            *[
                func_call
                for func_call in expected_sequence
                if func_call.name == tool.name
            ]
        ]
        for tool in tools
    }

    alphabet = {}
    general_generated: list[str] = []

    # create symbols for each unique function call in expected sequence
    for _, func_calls in used_tools.items():
        for func_call in func_calls:
            char = next(gen)
            alphabet[char] = func_call

        # create the general version of this function call with excluded values
        for func_call in func_calls:
            if func_call.name in general_generated:
                continue

            general_char = next(gen)
            general_arguments = {}
            # skip if no arguments
            if not func_call.arguments:
                continue
            for arg_name, arg in func_call.arguments.items():
                excluded_vals = [
                    fc.arguments[arg_name].value
                    for fc in func_calls
                    if arg_name in fc.arguments
                    and fc.arguments[arg_name].value is not None
                ]

                # Deduplicate excluded values in a way that supports unhashable types (e.g., lists)
                unique_excluded_vals = []
                seen = set()
                for v in excluded_vals:
                    key = repr(v)
                    if key in seen:
                        continue
                    seen.add(key)
                    unique_excluded_vals.append(v)

                general_arguments[arg_name] = FunctionArgument(
                    name=arg_name,
                    value=None,
                    excluded_values=unique_excluded_vals if unique_excluded_vals else None,
                    type=arg.type,
                )
            alphabet[general_char] = FunctionCall(
                name=func_call.name, arguments=general_arguments
            )
            general_generated.append(func_call.name)

    # add a symbol for unused tools
    for tool in tools:
        if tool.name not in used_tools or not used_tools[tool.name]:
            char = next(gen)
            if not tool.arguments:
                alphabet[char] = FunctionCall(name=tool.name, arguments={})
                continue
            general_arguments = {}
            for arg_name, arg_type in tool.arguments.items():
                general_arguments[arg_name] = FunctionArgument(
                            name=arg_name,
                            value=None,
                            excluded_values=None,
                            type=arg_type,
                        )
            alphabet[char] = FunctionCall(
                name=tool.name,
                arguments=general_arguments
            )

    return alphabet


def generate_dfa(
    expected_sequence: list[FunctionCall],
    alphabet: dict[str, FunctionCall],
    tools: list[ToolInfo],
) -> list[Node]:
    """
    Generate DFA from expected sequence and alphabet.

    Args:
        expected_sequence: Expected sequence of function calls
        alphabet: Symbol to function call mapping
        tools: Available tools/functions

    Returns:
        List of DFA nodes representing the state machine
    """

    nodes = []
    nodes.append(
        Node("G0"),
    )

    for index, tool in enumerate(expected_sequence):
        nodes.append(
            Node(f"G{index + 1}"),
        )
    nodes[-1].is_final = True

    for index, node in enumerate(nodes):
        node.transitions = []
        expected_tool = (
            expected_sequence[index] if index < len(expected_sequence) else None
        )
        self_loop_transition = Transition(symbols=[], _from=node, _to=node)

        for i, tool_call in enumerate(alphabet.items()):
            symbol, tc = tool_call

            # evaluate what happens in this state if the function is called
            if expected_tool is not None and tc.name == expected_tool.name:
                # check if the arguments match
                if all(
                    expected_tool.arguments.get(arg_name).value  # type: ignore
                    == tc.arguments.get(arg_name).value  # type: ignore
                    for arg_name in expected_tool.arguments
                ):
                    node.transitions.append(
                        Transition(
                            symbols=[symbol],
                            _from=node,
                            # stay in the same node if last node
                            _to=nodes[index + 1] if index + 1 < len(nodes) else node,
                        )
                    )
                    continue

            # if last iteration then append the self-loop transition
            if i == len(alphabet) - 1 and self_loop_transition.symbols:
                node.transitions.append(self_loop_transition)

    return nodes


def get_node_read_onlys(node: Node) -> list[str]:
    """
    Get the read-only actions for a given node.

    Args:
        node: DFA node to analyze

    Returns:
        List of read-only symbols for the node
    """
    read_onlys: list[str] = []
    for t in node.transitions:
        if t._to == t._from:
            read_onlys.extend(t.symbols)
    return read_onlys


def convert_dfa_to_single_symbol_transitions(dfa: list[Node]) -> list[Node]:
    """
    Convert DFA transitions to have only one symbol per transition.

    Args:
        dfa: The DFA represented as a list of Nodes.

    Returns:
        DFA with single-symbol transitions
    """
    _dfa = copy(dfa)
    for node in _dfa:
        new_transitions = []
        for transition in node.transitions:
            for symbol in transition.symbols:
                new_transitions.append(
                    Transition(
                        symbols=[symbol], _from=transition._from, _to=transition._to
                    )
                )
        node.transitions = new_transitions
    return _dfa





def simplify_and_mark(seq: list[str], dfa: list[Node]):
    """
    Simplify sequence and mark harmful actions.

    Args:
        seq: Sequence of symbols
        dfa: DFA nodes

    Returns:
        Tuple of (simplified_seq, marked_seq, fail_states)
    """
    dfa = convert_dfa_to_single_symbol_transitions(dfa)

    current = dfa[0]
    simplified_seq = []
    marked_seq = []

    fail_states = 0

    for idx, action in enumerate(seq):
        next_state = None

        for transition in current.transitions:
            if transition.symbols[0] == action:
                next_state = transition._to
                break

        if next_state is None:
            fail_states += 1
            simplified_seq.append(action)
            marked_seq.append("@")
            continue

        if not next_state.name == current.name:
            simplified_seq.append(action)
            marked_seq.append(action)

        current = next_state

    return simplified_seq, marked_seq, fail_states
