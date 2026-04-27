from pathlib import Path

from rsare.research_suite.executor import ScenarioRunConfig, run_single_scenario


def test_mock_smoke_for_four_new_families(tmp_path: Path):
    families = [
        "farm_rewoo_modular",
        "farm_tree_search",
        "farm_critic_refiner",
        "farm_graph_memory",
    ]
    for family in families:
        result = run_single_scenario(
            ScenarioRunConfig(
                run_id=f"test__{family}",
                pack_name="test_pack",
                family_id=family,
                scenario_id="scenario_farm_world_irrigation",
                model="mock-model",
                provider="mock",
                endpoint=None,
                output_dir=str(tmp_path / family),
                a2a_enabled=False,
            )
        )
        assert result["status"] == "ok"
        assert result["infra_pass"] is True
        assert result["telemetry"]["llm_calls"] > 0
