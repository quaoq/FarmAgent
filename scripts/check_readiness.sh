#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  RESOLVED_PYTHON_BIN="${PYTHON_BIN}"
elif [[ -x "${ROOT_DIR}/.venv312/bin/python" ]]; then
  RESOLVED_PYTHON_BIN="${ROOT_DIR}/.venv312/bin/python"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  RESOLVED_PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
elif [[ -x "$(cd "${ROOT_DIR}/.." && pwd)/FarmARE/.venv312/bin/python" ]]; then
  RESOLVED_PYTHON_BIN="$(cd "${ROOT_DIR}/.." && pwd)/FarmARE/.venv312/bin/python"
else
  RESOLVED_PYTHON_BIN="$(command -v python3 || command -v python)"
fi

echo "[check] repo root: ${ROOT_DIR}"
echo "[check] python: $(${RESOLVED_PYTHON_BIN} --version)"
cd "${ROOT_DIR}"

echo "[check] validating 10-family registry"
"${RESOLVED_PYTHON_BIN}" - <<'PY'
from rsare.research_suite.families import RESEARCH_FAMILY_IDS, build_family_profile

for family_id in RESEARCH_FAMILY_IDS:
    profile = build_family_profile(family_id)
    assert profile.family_id == family_id
print("registered families:", list(RESEARCH_FAMILY_IDS))
PY

echo "[check] validating scenario registry"
"${RESOLVED_PYTHON_BIN}" - <<'PY'
from rsare.research_suite.scenario_registry import list_registered_scenarios

required = {
    "scenario_farm_world_field_prep",
    "scenario_farm_world_irrigation",
    "scenario_farm_world_pesticide",
    "scenario_farm_world_harvest",
    "scenario_gma_0",
}
available = set(list_registered_scenarios())
missing = sorted(required - available)
if missing:
    raise SystemExit(f"Missing scenarios: {missing}")
print("registered scenarios:", sorted(required))
PY

echo "[check] validating suite dry-run expansion"
"${RESOLVED_PYTHON_BIN}" "${ROOT_DIR}/scripts/run_agent_suite.py" \
  --config "${ROOT_DIR}/configs/agent_suite/smoke.yaml" \
  --dry-run \
  --mock >/tmp/farmagent_suite_dry_run.json
echo "[check] dry-run manifest written to /tmp/farmagent_suite_dry_run.json"

echo "[check] validating expected pack names"
"${RESOLVED_PYTHON_BIN}" - <<'PY'
from pathlib import Path
from rsare.research_suite.suite_runner import load_suite_config, expand_run_specs

root = Path.cwd()
smoke = load_suite_config(root / "configs" / "agent_suite" / "smoke.yaml")
full = load_suite_config(root / "configs" / "agent_suite" / "full_compare.yaml")
smoke_specs = expand_run_specs(smoke, force_mock=True, enable_real_model_preflight=False)
full_specs = expand_run_specs(full, force_mock=True, enable_real_model_preflight=False)

smoke_packs = sorted({spec.pack_name for spec in smoke_specs})
full_packs = sorted({spec.pack_name for spec in full_specs})
expected_smoke = ["smoke_a2a_off", "smoke_a2a_on_typed"]
expected_full = ["full_compare_a2a_off", "full_compare_a2a_on_typed"]
if smoke_packs != expected_smoke:
    raise SystemExit(f"Unexpected smoke packs: {smoke_packs}")
if full_packs != expected_full:
    raise SystemExit(f"Unexpected full packs: {full_packs}")
print("smoke packs:", smoke_packs)
print("full packs:", full_packs)
PY

echo "[check] readiness checks passed"
