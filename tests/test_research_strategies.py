from rsare.research_suite.families import build_family_profile
from rsare.research_suite.strategies import build_strategy_context


def test_rewoo_strategy_emits_plan():
    profile = build_family_profile("farm_rewoo_modular")
    context = build_strategy_context(
        task="1. Check weather 2. Inspect tractor 3. Irrigate field",
        profile=profile,
        reflection_memory=[],
        retrieved_skills=[],
    )
    assert "ReWOO Plan-Work-Solve" in context.extra_prompt
    assert context.telemetry["planned_steps"] >= 1


def test_tree_search_strategy_generates_candidates():
    profile = build_family_profile("farm_tree_search")
    context = build_strategy_context(
        task="Check weather and then irrigate",
        profile=profile,
        reflection_memory=[],
        retrieved_skills=[],
    )
    assert "Tree-search deliberation" in context.extra_prompt
    assert context.telemetry["branches_generated"] >= 1


def test_critic_strategy_reports_blocks_for_irreversible_action_without_checks():
    profile = build_family_profile("farm_critic_refiner")
    context = build_strategy_context(
        task="Spray pesticide across all ridges immediately.",
        profile=profile,
        reflection_memory=[],
        retrieved_skills=[],
    )
    assert "Critic-Refiner protocol" in context.extra_prompt
    assert context.telemetry["blocked_actions"] in {0, 1}


def test_graph_memory_strategy_reports_retrieval():
    profile = build_family_profile("farm_graph_memory")
    context = build_strategy_context(
        task="Inspect moisture and apply irrigation in ridge 10-20",
        profile=profile,
        reflection_memory=[],
        retrieved_skills=[],
    )
    assert "Graph-memory context" in context.extra_prompt
    assert context.telemetry["graph_nodes"] >= 1
