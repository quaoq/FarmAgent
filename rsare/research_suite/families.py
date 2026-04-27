from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SkillConfig:
    enabled: bool = False
    top_k: int = 3
    min_score: float = 0.12
    library_path: str = "rsare/research_suite/skills"


@dataclass(frozen=True)
class ReflectionConfig:
    enabled: bool = False
    max_items: int = 6
    injection_top_k: int = 2


@dataclass(frozen=True)
class DelegationConfig:
    enabled: bool = False
    specialists: tuple[str, ...] = (
        "Weather specialist",
        "Sensors specialist",
        "Machinery specialist",
        "Operations specialist",
    )


@dataclass(frozen=True)
class VerificationConfig:
    enabled: bool = False
    uncertainty_keywords: tuple[str, ...] = (
        "not sure",
        "unclear",
        "unknown",
        "maybe",
        "risk",
    )


@dataclass(frozen=True)
class ReWOOConfig:
    enabled: bool = False
    max_plan_steps: int = 8
    max_replans: int = 1


@dataclass(frozen=True)
class TreeSearchConfig:
    enabled: bool = False
    branch_factor: int = 3
    search_depth: int = 2
    max_expansions: int = 6


@dataclass(frozen=True)
class CriticConfig:
    enabled: bool = False
    max_revision_cycles: int = 2
    enforce_precondition_checks: bool = True


@dataclass(frozen=True)
class GraphMemoryConfig:
    enabled: bool = False
    max_nodes: int = 60
    retrieval_top_k: int = 5
    contradiction_check: bool = True


@dataclass(frozen=True)
class ResearchAgentProfileConfig:
    family_id: str
    display_name: str
    summary: str
    system_prompt_suffix: str = ""
    planning_mode: str = "react"
    reflection: ReflectionConfig = field(default_factory=ReflectionConfig)
    skills: SkillConfig = field(default_factory=SkillConfig)
    delegation: DelegationConfig = field(default_factory=DelegationConfig)
    verification: VerificationConfig = field(default_factory=VerificationConfig)
    rewoo: ReWOOConfig = field(default_factory=ReWOOConfig)
    tree_search: TreeSearchConfig = field(default_factory=TreeSearchConfig)
    critic: CriticConfig = field(default_factory=CriticConfig)
    graph_memory: GraphMemoryConfig = field(default_factory=GraphMemoryConfig)


RESEARCH_FAMILY_IDS: tuple[str, ...] = (
    "farm_baseline_react",
    "farm_planner_executor",
    "farm_reflective_memory",
    "farm_skill_rag",
    "farm_multi_specialist",
    "farm_adaptive_verifier",
    "farm_rewoo_modular",
    "farm_tree_search",
    "farm_critic_refiner",
    "farm_graph_memory",
)


def get_default_skill_library_path() -> str:
    return str(Path("rsare") / "research_suite" / "skills")


def build_family_profile(family_id: str) -> ResearchAgentProfileConfig:
    skill_path = get_default_skill_library_path()
    match family_id:
        case "farm_baseline_react":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Baseline ReAct",
                summary="Plain tool-using ReAct baseline for farm tasks.",
            )
        case "farm_planner_executor":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Planner-Executor",
                summary="Creates an explicit task plan before execution.",
                planning_mode="planner_executor",
                system_prompt_suffix=(
                    "Always draft a short numbered plan, then execute one step at a time."
                ),
            )
        case "farm_reflective_memory":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Reflective Memory",
                summary="Writes compact lessons and injects them in later decisions.",
                reflection=ReflectionConfig(enabled=True),
                system_prompt_suffix=(
                    "Reflect after key actions and reuse lessons to avoid repeated mistakes."
                ),
            )
        case "farm_skill_rag":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Skill RAG",
                summary="Retrieves local procedural skills and executes matching playbooks.",
                skills=SkillConfig(enabled=True, library_path=skill_path),
                system_prompt_suffix=(
                    "Prefer retrieved procedural skills when they match the current farm task."
                ),
            )
        case "farm_multi_specialist":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Multi-Specialist",
                summary="Simulates domain specialists and merges recommendations.",
                delegation=DelegationConfig(enabled=True),
                system_prompt_suffix=(
                    "Reason as weather, sensor, machinery, and operations specialists before acting."
                ),
            )
        case "farm_adaptive_verifier":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Adaptive Verifier",
                summary="Adds uncertainty-triggered verification before irreversible actions.",
                verification=VerificationConfig(enabled=True),
                system_prompt_suffix=(
                    "When uncertain, verify preconditions and safety before tool calls."
                ),
            )
        case "farm_rewoo_modular":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="ReWOO Modular",
                summary="Plan-Work-Solve decomposition with structured step execution.",
                planning_mode="planner_executor",
                rewoo=ReWOOConfig(enabled=True),
            )
        case "farm_tree_search":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Tree Search",
                summary="Generates and scores candidate branches; supports one backtrack.",
                tree_search=TreeSearchConfig(enabled=True),
            )
        case "farm_critic_refiner":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Critic Refiner",
                summary="Actor proposal with critic revisions and precondition gating.",
                critic=CriticConfig(enabled=True),
            )
        case "farm_graph_memory":
            return ResearchAgentProfileConfig(
                family_id=family_id,
                display_name="Graph Memory",
                summary="Maintains structured task-state memory graph and contradiction checks.",
                graph_memory=GraphMemoryConfig(enabled=True),
            )
        case _:
            raise ValueError(f"Unsupported research family: {family_id}")
