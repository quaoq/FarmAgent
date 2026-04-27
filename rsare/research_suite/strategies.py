from __future__ import annotations

import re
from dataclasses import dataclass

from rsare.research_suite.families import ResearchAgentProfileConfig


@dataclass
class StrategyContext:
    extra_prompt: str
    telemetry: dict[str, int | float | str | list[str]]


def _parse_steps(text: str, max_steps: int) -> list[str]:
    numbered = re.findall(r"^\s*(?:\d+[\).\-\:])\s*(.+?)\s*$", text, re.MULTILINE)
    if not numbered:
        numbered = [chunk.strip() for chunk in re.split(r"[\n\.]+", text) if chunk.strip()]
    cleaned: list[str] = []
    for step in numbered:
        normalized = step.strip()
        if len(normalized) < 4 or normalized in cleaned:
            continue
        cleaned.append(normalized)
        if len(cleaned) >= max(1, max_steps):
            break
    return cleaned


def _score_candidate(plan: str) -> float:
    lowered = plan.lower()
    score = 1.0
    if "check weather" in lowered or "weather" in lowered:
        score += 0.3
    if "check sensor" in lowered or "sensor" in lowered:
        score += 0.3
    if "verify" in lowered or "precondition" in lowered:
        score += 0.4
    if "immediately" in lowered:
        score -= 0.2
    return score


def build_strategy_context(
    task: str,
    profile: ResearchAgentProfileConfig,
    reflection_memory: list[str],
    retrieved_skills: list[str],
) -> StrategyContext:
    telemetry: dict[str, int | float | str | list[str]] = {
        "planner_calls": 0,
        "planned_steps": 0,
        "executed_steps": 0,
        "plan_parse_failures": 0,
        "branches_generated": 0,
        "branches_scored": 0,
        "backtracks": 0,
        "critic_cycles": 0,
        "revision_cycles": 0,
        "blocked_actions": 0,
        "graph_nodes": 0,
        "graph_edges": 0,
        "graph_retrieval_hits": 0,
        "contradiction_alerts": 0,
    }
    context_parts: list[str] = []

    if profile.planning_mode == "planner_executor":
        context_parts.append(
            "Planner-Executor protocol: produce a concise numbered plan and execute one milestone at a time."
        )

    if profile.reflection.enabled and reflection_memory:
        recent = reflection_memory[-profile.reflection.injection_top_k :]
        context_parts.append("Reflection memory:\n" + "\n".join(f"- {line}" for line in recent))

    if profile.skills.enabled and retrieved_skills:
        context_parts.append("Retrieved skills:\n" + "\n".join(f"- {line}" for line in retrieved_skills))

    if profile.delegation.enabled:
        specialists = ", ".join(profile.delegation.specialists)
        context_parts.append(
            f"Specialist decomposition: simulate recommendations from [{specialists}] before final action."
        )

    if profile.verification.enabled:
        cues = ", ".join(profile.verification.uncertainty_keywords)
        context_parts.append(
            "Adaptive verification rule: when uncertainty appears, run an explicit precondition check first. "
            f"Uncertainty cues: {cues}."
        )

    if profile.rewoo.enabled:
        telemetry["planner_calls"] = int(telemetry["planner_calls"]) + 1
        steps = _parse_steps(task, profile.rewoo.max_plan_steps)
        if not steps:
            telemetry["plan_parse_failures"] = int(telemetry["plan_parse_failures"]) + 1
            context_parts.append(
                "ReWOO fallback: no robust plan parse; continue with explicit Plan->Work->Solve headings."
            )
        else:
            telemetry["planned_steps"] = len(steps)
            telemetry["executed_steps"] = len(steps)
            rendered = "\n".join(f"- Step {index + 1}: {step}" for index, step in enumerate(steps))
            context_parts.append(
                "ReWOO Plan-Work-Solve:\n"
                f"{rendered}\n"
                "- Execute each step with available tools and summarize evidence in the final answer."
            )

    if profile.tree_search.enabled:
        base_steps = _parse_steps(task, max(2, profile.tree_search.search_depth + 1))
        if not base_steps:
            base_steps = ["Inspect state", "Validate preconditions", "Execute next action"]
        candidates: list[tuple[str, float]] = []
        for branch_index in range(max(1, profile.tree_search.branch_factor)):
            if branch_index == 0:
                plan = " -> ".join(base_steps[: profile.tree_search.search_depth + 1])
            elif branch_index == 1:
                plan = " -> ".join(["Check weather and sensors", *base_steps[: profile.tree_search.search_depth]])
            else:
                plan = " -> ".join(["Verify inventory and machine readiness", *base_steps[: profile.tree_search.search_depth]])
            candidates.append((plan, _score_candidate(plan)))
        candidates.sort(key=lambda row: row[1], reverse=True)
        telemetry["branches_generated"] = len(candidates)
        telemetry["branches_scored"] = len(candidates)
        rendered = "\n".join(
            f"- Candidate {index + 1} (score={score:.2f}): {plan}"
            for index, (plan, score) in enumerate(candidates)
        )
        context_parts.append(
            "Tree-search deliberation:\n"
            f"{rendered}\n"
            "- Execute highest-scoring candidate first; backtrack once if hard failure occurs."
        )

    if profile.critic.enabled:
        telemetry["critic_cycles"] = 1
        telemetry["revision_cycles"] = profile.critic.max_revision_cycles
        has_precondition_words = bool(
            re.search(r"\b(check|verify|confirm|inspect)\b", task, re.IGNORECASE)
        )
        irreversible = bool(
            re.search(r"\b(spray|plant|fertiliz|harvest|irrigat|apply)\w*\b", task, re.IGNORECASE)
        )
        blocked = (
            profile.critic.enforce_precondition_checks and irreversible and not has_precondition_words
        )
        telemetry["blocked_actions"] = 1 if blocked else 0
        context_parts.append(
            "Critic-Refiner protocol:\n"
            "- Actor proposes one next action.\n"
            "- Critic checks weather, tool readiness, safety, and irreversible-action preconditions.\n"
            f"- Revision cycles: {profile.critic.max_revision_cycles}.\n"
            f"- Block irreversible action until checks pass: {'yes' if blocked else 'no'}."
        )

    if profile.graph_memory.enabled:
        objective_nodes = _parse_steps(task, 3) or [task[:180]]
        graph_nodes = [f"[objective] {node}" for node in objective_nodes]
        telemetry["graph_nodes"] = min(len(graph_nodes), profile.graph_memory.max_nodes)
        telemetry["graph_edges"] = max(0, int(telemetry["graph_nodes"]) - 1)
        hits = min(len(graph_nodes), profile.graph_memory.retrieval_top_k)
        telemetry["graph_retrieval_hits"] = hits
        merged = " ".join(graph_nodes).lower()
        contradiction = bool(
            ("no rain" in merged and "rain" in merged)
            or ("wet" in merged and "dry" in merged)
        )
        telemetry["contradiction_alerts"] = 1 if contradiction else 0
        context_parts.append(
            "Graph-memory context:\n"
            + "\n".join(f"- {node}" for node in graph_nodes[: profile.graph_memory.retrieval_top_k])
            + "\n"
            + f"- Contradiction alert: {'detected' if contradiction else 'none'}."
        )

    return StrategyContext(
        extra_prompt="\n\n".join(part for part in context_parts if part.strip()),
        telemetry=telemetry,
    )
