from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import uuid4

from rsare.agents.llm.base_llm import BaseLLM


@dataclass
class _PromptTokensDetails:
    cached_tokens: int = 0


@dataclass
class _Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: _PromptTokensDetails


@dataclass
class _ToolFunction:
    name: str
    arguments: str


@dataclass
class _ToolCall:
    id: str
    type: str
    function: _ToolFunction


@dataclass
class _Message:
    content: str | None = None
    tool_calls: list[_ToolCall] | None = None


@dataclass
class _Choice:
    message: _Message


@dataclass
class _Response:
    choices: list[_Choice]
    usage: _Usage


class MockLLM(BaseLLM):
    llm_class = "MockLLM"

    def __init__(self, model: str = "mock-model", temperature: float = 0.0, **kwargs):
        super().__init__(model, temperature, **kwargs)
        self.provider = "mock"
        self._planned_steps: list[dict] = []
        self._cursor = 0

    def set_plan(self, planned_steps: list[dict]) -> None:
        self._planned_steps = list(planned_steps)
        self._cursor = 0

    def _usage(self, prompt_tokens: int = 12, completion_tokens: int = 8) -> _Usage:
        return _Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            prompt_tokens_details=_PromptTokensDetails(cached_tokens=0),
        )

    def _resolve_tool_name(self, requested_name: str, tools: list[dict] | None) -> str:
        if not tools:
            return requested_name
        available = [item.get("function", {}).get("name", "") for item in tools]
        if requested_name in available:
            return requested_name
        suffix = f"__{requested_name}"
        for candidate in available:
            if candidate.endswith(suffix):
                return candidate
        return requested_name

    def _filter_args(
        self, tool_name: str, tool_args: dict, tools: list[dict] | None
    ) -> dict:
        if not tools:
            return tool_args
        for tool in tools:
            fn = tool.get("function", {})
            if fn.get("name") != tool_name:
                continue
            props = (
                fn.get("parameters", {}).get("properties", {})
                if isinstance(fn.get("parameters"), dict)
                else {}
            )
            if not props:
                return tool_args
            return {key: value for key, value in tool_args.items() if key in props}
        return tool_args

    def chat_completion(self, messages, tools=None):
        if self._cursor < len(self._planned_steps):
            step = self._planned_steps[self._cursor]
            self._cursor += 1
            requested_tool = str(step.get("tool_name", ""))
            args = dict(step.get("tool_args", {}) or {})
            resolved_tool = self._resolve_tool_name(requested_tool, tools)
            filtered_args = self._filter_args(resolved_tool, args, tools)
            message = _Message(
                content=None,
                tool_calls=[
                    _ToolCall(
                        id=f"mock_tool_{uuid4().hex[:10]}",
                        type="function",
                        function=_ToolFunction(
                            name=resolved_tool,
                            arguments=json.dumps(filtered_args),
                        ),
                    )
                ],
            )
            return _Response(choices=[_Choice(message=message)], usage=self._usage())

        final_message = _Message(content="Mock execution complete.", tool_calls=None)
        return _Response(choices=[_Choice(message=final_message)], usage=self._usage())
