from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rsare.agents.agent.agent import Agent
from rsare.agents.llm.base_llm import BaseLLM
from rsare.agents.llm.openai_llm import OpenAILLM
from rsare.engine.engine import Engine
from rsare.research_suite.a2a import apply_a2a_conversion
from rsare.research_suite.families import ResearchAgentProfileConfig, build_family_profile
from rsare.research_suite.mock_llm import MockLLM
from rsare.research_suite.scenario_registry import create_scenario
from rsare.research_suite.skill_library import DynamicSkillLibrary
from rsare.research_suite.strategies import build_strategy_context
from rsare.validation.metrics import path_correctness


@dataclass(frozen=True)
class ScenarioRunConfig:
    run_id: str
    pack_name: str
    family_id: str
    scenario_id: str
    model: str
    provider: str
    endpoint: str | None
    output_dir: str
    export: bool = True
    temperature: float = 0.1
    a2a_enabled: bool = False
    a2a_app_prop: float = 0.0
    a2a_policy: str = "generic"
    a2a_app_agent: str = "default_app_agent"
    model_resolution: str = "profile"


def _extract_tool_steps(workflow) -> list[dict[str, Any]]:
    dag = workflow.dag if hasattr(workflow, "dag") else workflow
    values = dag.values() if isinstance(dag, dict) else dag
    results: list[dict[str, Any]] = []
    for step in values:
        if isinstance(step, dict):
            tool_name = step.get("tool_name")
            tool_args = step.get("tool_args", {}) or {}
            op_type = step.get("op_type")
        else:
            tool_name = getattr(step, "tool_name", None)
            tool_args = getattr(step, "tool_args", {}) or {}
            op_type = getattr(step, "op_type", None)
        if not tool_name or op_type == "USER":
            continue
        results.append({"tool_name": str(tool_name), "tool_args": dict(tool_args)})
    return results


def _step_token(step: dict[str, Any]) -> str:
    args = json.dumps(step.get("tool_args", {}), sort_keys=True)
    return f"{step.get('tool_name')}::{args}"


def _resolve_toolsets(scenario) -> list[Any]:
    if getattr(scenario, "apps", None):
        return list(scenario.apps)
    if hasattr(scenario, "sarTools") and scenario.sarTools is not None:
        return [scenario.sarTools, scenario]
    return [scenario]


def _build_system_prompt(profile: ResearchAgentProfileConfig) -> str:
    base = (
        "You are a research-grade farm operations agent. "
        "Use available tools carefully, respect preconditions, and report concise outcomes."
    )
    if profile.system_prompt_suffix:
        return f"{base}\n{profile.system_prompt_suffix}"
    return base


def _build_llm(
    provider: str,
    model: str,
    temperature: float,
    endpoint: str | None,
    oracle_steps: list[dict[str, Any]],
) -> BaseLLM:
    normalized_provider = provider.lower().strip()
    if normalized_provider == "mock":
        llm = MockLLM(model=model, temperature=temperature)
        llm.set_plan(oracle_steps)
        return llm
    if normalized_provider in {"openai", "llama-api", "default"}:
        api_base = endpoint or os.getenv("OPENAI_BASE_URL")
        return OpenAILLM(model=model, temperature=temperature, base_url=api_base)
    return BaseLLM.llm_builder(
        {
            "provider": normalized_provider,
            "model": model,
            "temperature": temperature,
            "base_url": endpoint,
        }
    )


def _derive_infra_flags(
    status: str,
    error_message: str | None,
    llm_calls: int,
    trace_exported: bool,
) -> dict[str, bool]:
    error_text = (error_message or "").lower()
    auth_markers = [
        "invalid api key",
        "auth",
        "unauthorized",
        "forbidden",
        "error code: 401",
        "insufficient_quota",
        "geography restrictions enabled",
    ]
    connectivity_markers = [
        "connection",
        "timeout",
        "name resolution",
        "network",
        "max retries exceeded",
    ]
    has_auth_issue = any(marker in error_text for marker in auth_markers)
    has_connectivity_issue = any(marker in error_text for marker in connectivity_markers)
    return {
        "infra_exit_ok": status in {"ok", "success"},
        "infra_auth_ok": not has_auth_issue,
        "infra_connectivity_ok": not has_connectivity_issue,
        "infra_llm_calls_positive": llm_calls > 0,
        "infra_trace_exported": trace_exported,
    }


def run_single_scenario(config: ScenarioRunConfig) -> dict[str, Any]:
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    profile = build_family_profile(config.family_id)

    # Build oracle run on a clean scenario instance.
    oracle_scenario = create_scenario(config.scenario_id)
    if hasattr(oracle_scenario, "initiate_scenario"):
        oracle_scenario.initiate_scenario()
    oracle_scenario.oracle_solution(run_oracle=False)
    oracle_steps = _extract_tool_steps(oracle_scenario.workflow)

    # Build agent run on a second fresh scenario instance.
    scenario = create_scenario(config.scenario_id)
    if hasattr(scenario, "initiate_scenario"):
        scenario.initiate_scenario()
    toolsets = _resolve_toolsets(scenario)

    telemetry: dict[str, Any] = {
        "family_id": profile.family_id,
        "planning_mode": profile.planning_mode,
        "llm_calls": 0,
        "tool_calls": 0,
        "latency_seconds": 0.0,
        "memory_reads": 0,
        "memory_writes": 0,
        "skill_hits": 0,
        "retrieved_skill_ids": [],
        "delegation_signals": 0,
        "verification_signals": 0,
        "a2a_tool_calls": 0,
    }

    converted_apps = []
    if getattr(scenario, "apps", None):
        converted_apps = apply_a2a_conversion(
            apps=scenario.apps,
            enabled=config.a2a_enabled,
            app_prop=config.a2a_app_prop,
            policy=config.a2a_policy,
            fallback_app_agent=config.a2a_app_agent,
            telemetry=telemetry,
        )

    skill_lines: list[str] = []
    if profile.skills.enabled:
        skill_library = DynamicSkillLibrary(profile.skills.library_path)
        for record, score in skill_library.retrieve(
            getattr(scenario, "scenario_input", ""),
            top_k=profile.skills.top_k,
            min_score=profile.skills.min_score,
        ):
            line = f"{record.skill_id} (score={score:.2f}) {record.title}"
            skill_lines.append(line)
            telemetry["retrieved_skill_ids"].append(record.skill_id)
        telemetry["skill_hits"] = len(skill_lines)

    reflection_memory: list[str] = []
    if profile.reflection.enabled:
        for step in oracle_steps[: profile.reflection.max_items]:
            reflection_memory.append(
                f"After {step['tool_name']}, confirm outcome before next irreversible action."
            )
        telemetry["memory_writes"] = len(reflection_memory)
        if reflection_memory:
            telemetry["memory_reads"] = min(
                len(reflection_memory), profile.reflection.injection_top_k
            )

    strategy = build_strategy_context(
        task=getattr(scenario, "scenario_input", ""),
        profile=profile,
        reflection_memory=reflection_memory,
        retrieved_skills=skill_lines,
    )
    telemetry.update(strategy.telemetry)
    if profile.delegation.enabled:
        telemetry["delegation_signals"] = 1
    if profile.verification.enabled:
        telemetry["verification_signals"] = 1

    llm = _build_llm(
        provider=config.provider,
        model=config.model,
        temperature=config.temperature,
        endpoint=config.endpoint,
        oracle_steps=oracle_steps,
    )
    task_input = getattr(scenario, "scenario_input", "")
    if strategy.extra_prompt.strip():
        task_input = f"{task_input}\n\n{strategy.extra_prompt}"

    agent = Agent(
        name=config.family_id,
        llm=llm,
        system_message=_build_system_prompt(profile),
        toolsets=toolsets,
    )
    Engine(agent, scenario)

    status = "ok"
    error_message = None
    try:
        agent.run(task_input)
    except Exception as error:  # pragma: no cover - external/runtime behavior
        status = "failed"
        error_message = str(error)

    runtime_metrics = getattr(agent.messages, "runtime_metrics", [])
    llm_calls = sum(1 for row in runtime_metrics if row.get("role") == "assistant")
    tool_calls = sum(1 for row in runtime_metrics if row.get("role") == "tool")
    latency = sum(float(row.get("time", 0.0)) for row in runtime_metrics)
    telemetry["llm_calls"] = llm_calls
    telemetry["tool_calls"] = tool_calls
    telemetry["latency_seconds"] = round(latency, 4)

    agent_steps = _extract_tool_steps(agent.workflow)
    oracle_tokens = [_step_token(step) for step in oracle_steps]
    agent_tokens = [_step_token(step) for step in agent_steps]
    score = path_correctness(agent_tokens, oracle_tokens)

    oracle_trace = output_dir / "workflow_oracle.json"
    agent_trace = output_dir / "workflow_agent.json"
    with open(oracle_trace, "w", encoding="utf-8") as handle:
        json.dump(oracle_scenario.workflow.to_dict(), handle, indent=2)
    with open(agent_trace, "w", encoding="utf-8") as handle:
        json.dump(agent.workflow.to_dict(), handle, indent=2)

    trace_exported = oracle_trace.exists() and agent_trace.exists()
    infra = _derive_infra_flags(
        status=status,
        error_message=error_message,
        llm_calls=llm_calls,
        trace_exported=trace_exported,
    )
    infra_pass = (
        infra["infra_exit_ok"]
        and infra["infra_auth_ok"]
        and infra["infra_connectivity_ok"]
        and infra["infra_llm_calls_positive"]
        and infra["infra_trace_exported"]
    )

    a2a_calls_by_expert = telemetry.get("a2a_calls_by_expert", {})
    if not isinstance(a2a_calls_by_expert, dict):
        a2a_calls_by_expert = dict(a2a_calls_by_expert)
    telemetry["a2a_calls_by_expert"] = dict(a2a_calls_by_expert)

    result = {
        "run_id": config.run_id,
        "pack_name": config.pack_name,
        "family": config.family_id,
        "scenario_id": config.scenario_id,
        "model": config.model,
        "provider": config.provider,
        "endpoint": config.endpoint,
        "model_resolution": config.model_resolution,
        "status": status,
        "error": error_message,
        "score": round(float(score), 4),
        "output_dir": str(output_dir),
        "oracle_trace_path": str(oracle_trace),
        "agent_trace_path": str(agent_trace),
        "a2a_enabled": config.a2a_enabled,
        "a2a_policy": config.a2a_policy,
        "a2a_app_prop": config.a2a_app_prop,
        "a2a_app_agent": config.a2a_app_agent,
        "a2a_converted_apps": converted_apps,
        "telemetry": telemetry,
        **infra,
        "infra_pass": infra_pass,
    }
    with open(output_dir / "output.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    with open(output_dir / "config.json", "w", encoding="utf-8") as handle:
        json.dump(asdict(config), handle, indent=2)
    return result
