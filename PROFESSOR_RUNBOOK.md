# Professor Runbook (FarmAgent)

This runbook is for **architecture-comparison execution**, not benchmark claiming.  
Default path is no-key mock mode. Real-model mode is optional.

## 1) Local Setup (uv-first, no Docker)

### Option A (recommended): `uv`
```bash
uv sync
```

### Option B: pip fallback
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Environment file

```bash
cp .env.example.professor .env
```

- Leave keys empty for `--mock`.
- Add `OPENAI_API_KEY` (and optional `OPENAI_BASE_URL`) for `--real`.

## 3) Readiness check (non-destructive)

```bash
uv run ./scripts/check_readiness.sh
```

Checks include:
- 10 family registry,
- scenario registry,
- suite config expansion,
- expected A2A OFF/ON pack wiring.

## 4) 5-minute no-key smoke

Dry-run only:
```bash
uv run python scripts/run_agent_suite.py --config configs/agent_suite/smoke.yaml --dry-run --mock
```

Execute smoke:
```bash
uv run python scripts/run_agent_suite.py --config configs/agent_suite/smoke.yaml --mock
```

Smoke includes:
- `smoke_a2a_off`
- `smoke_a2a_on_typed`

## 5) Real-model smoke (optional)

```bash
uv run python scripts/run_agent_suite.py --config configs/agent_suite/smoke.yaml --real
```

Resolver behavior in real mode:
- tries `o4-mini`,
- falls back to `gpt-4o-mini` if needed,
- records selected model resolution in artifacts.

## 6) Run a single family

Example:
```bash
uv run python scripts/run_agent_suite.py \
  --config configs/agent_suite/smoke.yaml \
  --mock \
  --family farm_graph_memory
```

You can repeat `--family` to select multiple families.

## 7) Full comparison matrix

```bash
uv run python scripts/run_agent_suite.py --config configs/agent_suite/full_compare.yaml --mock
```

Real mode:
```bash
uv run python scripts/run_agent_suite.py --config configs/agent_suite/full_compare.yaml --real
```

## 8) A2A modes

- OFF: baseline run (no app conversion)
- ON typed: deterministic app->expert routing
  - `WeatherApp` -> `weather_expert_app_agent`
  - `SensorApp` -> `sensor_expert_app_agent`
  - `TractorApp`/`FieldOpsApp` -> `machinery_expert_app_agent`
  - `FarmWorldApp`/`DroneApp`/`RobotApp` -> `operations_expert_app_agent`

## 9) Output artifacts

Suite outputs:
- `outputs/agent_suite_runs/<timestamp>/suite_manifest.json`
- `outputs/agent_suite_runs/<timestamp>/suite_results.json`
- `outputs/agent_suite_runs/<timestamp>/suite_results.csv`

Per-run directory contains:
- `workflow_oracle.json`
- `workflow_agent.json`
- `output.json`

## 10) How to interpret results

- `infra_pass`: release-gate health for smoke readiness.
- `score`: task-level oracle matching signal (informational during smoke).
- `telemetry_*`: architecture-specific counters (planning/search/critic/graph/A2A).

For handoff readiness, prioritize **infra pass rate** first, then inspect score patterns.
If commands behave differently across terminals, rerun with `uv run ...` to force the project environment.
