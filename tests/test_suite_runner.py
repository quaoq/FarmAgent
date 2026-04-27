from pathlib import Path

from rsare.research_suite.suite_runner import expand_run_specs, load_suite_config


def test_suite_runner_expansion_is_deterministic():
    repo_root = Path(__file__).resolve().parents[1]
    config = load_suite_config(repo_root / "configs" / "agent_suite" / "smoke.yaml")
    specs_a = expand_run_specs(
        config=config,
        force_mock=True,
        enable_real_model_preflight=False,
    )
    specs_b = expand_run_specs(
        config=config,
        force_mock=True,
        enable_real_model_preflight=False,
    )
    assert [spec.run_id for spec in specs_a] == [spec.run_id for spec in specs_b]
    assert any(spec.a2a_enabled for spec in specs_a)
    assert any(not spec.a2a_enabled for spec in specs_a)
