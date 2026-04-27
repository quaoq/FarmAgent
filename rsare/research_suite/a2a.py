from __future__ import annotations

import functools
import inspect
from collections import defaultdict
from typing import Any


APP_EXPERT_MAPPING: dict[str, str] = {
    "WeatherApp": "weather_expert_app_agent",
    "SensorApp": "sensor_expert_app_agent",
    "TractorApp": "machinery_expert_app_agent",
    "FieldOpsApp": "machinery_expert_app_agent",
    "FarmWorldApp": "operations_expert_app_agent",
    "DroneApp": "operations_expert_app_agent",
    "RobotApp": "operations_expert_app_agent",
}


def resolve_app_expert(app: Any, policy: str, fallback_agent: str) -> str:
    if policy == "typed_experts":
        return APP_EXPERT_MAPPING.get(app.__class__.__name__, fallback_agent)
    return fallback_agent


def _wrap_tool_method(
    app: Any,
    method_name: str,
    expert_agent: str,
    telemetry: dict[str, Any],
) -> None:
    current = getattr(app, method_name)
    if not callable(current):
        return
    if not getattr(current, "is_agent_tool", False):
        return
    if getattr(current, "_a2a_wrapped", False):
        return

    signature = inspect.signature(current)

    @functools.wraps(current)
    def wrapped(*args, **kwargs):
        telemetry["a2a_tool_calls"] = int(telemetry.get("a2a_tool_calls", 0)) + 1
        calls_by_expert = telemetry.setdefault("a2a_calls_by_expert", defaultdict(int))
        if isinstance(calls_by_expert, defaultdict):
            calls_by_expert[expert_agent] += 1
        return current(*args, **kwargs)

    wrapped.__signature__ = signature  # type: ignore[attr-defined]
    wrapped.is_agent_tool = True  # type: ignore[attr-defined]
    wrapped._a2a_wrapped = True  # type: ignore[attr-defined]
    setattr(app, method_name, wrapped)


def apply_a2a_conversion(
    apps: list[Any],
    enabled: bool,
    app_prop: float,
    policy: str,
    fallback_app_agent: str,
    telemetry: dict[str, Any],
) -> list[dict[str, str]]:
    if not enabled or not apps:
        return []

    app_candidates = [app for app in apps if app.__class__.__name__ != "SystemApp"]
    if not app_candidates:
        return []

    count = int(len(app_candidates) * app_prop)
    if app_prop > 0 and count == 0:
        count = 1
    count = min(len(app_candidates), max(0, count))
    selected = sorted(app_candidates, key=lambda app: app.name)[:count]

    converted: list[dict[str, str]] = []
    for app in selected:
        expert_agent = resolve_app_expert(app, policy, fallback_app_agent)
        for attr_name in dir(app):
            _wrap_tool_method(app, attr_name, expert_agent, telemetry)
        converted.append(
            {
                "app_name": app.name,
                "app_type": app.__class__.__name__,
                "expert_agent": expert_agent,
            }
        )

    return converted
