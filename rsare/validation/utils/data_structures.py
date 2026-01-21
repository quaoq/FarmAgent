"""
Data structures for CORE scenario validation.

This module contains all the dataclasses and type definitions
used throughout the validation system.
"""

from dataclasses import dataclass, field
from typing import Any

@dataclass
class Node:
    """Represents a state in the DFA."""

    name: str
    transitions: list["Transition"] = field(default_factory=list)
    is_final: bool = False


@dataclass
class Transition:
    """Represents a transition between DFA states."""

    symbols: list[str]
    _from: Node
    _to: Node

    def __repr__(self):
        symbols_str = ", ".join(self.symbols)
        return f"Transition(on: [{symbols_str}] to: {self._to.name})"



@dataclass
class FunctionArgument:
    """Represents an argument to a function call."""

    name: str
    value: Any | None
    excluded_values: list[Any] | None
    type: str


@dataclass
class FunctionCall:
    """Represents a function call with arguments."""

    name: str
    arguments: dict[str, FunctionArgument]



@dataclass
class ToolInfo:
    """Information about a tool/function."""

    name: str
    arguments: dict[str, str]  # argument name to type mapping

