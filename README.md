# FarmAgent

Research-oriented agent architecture suite for farm + control scenarios.

## What is included

- 10 research controller families (ReAct baseline + planning/memory/RAG/search/critic/graph variants)
- A2A ON/OFF experiment packs with typed app-expert policy
- Mock mode (no key) and real mode (OpenAI-compatible) in one runner
- Structured JSON/CSV outputs for later paper analysis

## Quick start

```bash
uv sync
# or: pip install -r requirements.txt
uv run ./scripts/check_readiness.sh
uv run python scripts/run_agent_suite.py --config configs/agent_suite/smoke.yaml --mock
```

## Key docs

- `AGENT_FAMILIES_AND_PAPERS.md`
- `PROFESSOR_RUNBOOK.md`

## Main experiment interface

```bash
uv run python scripts/run_agent_suite.py --config configs/agent_suite/smoke.yaml --dry-run --mock
uv run python scripts/run_agent_suite.py --config configs/agent_suite/full_compare.yaml --mock
uv run python scripts/run_agent_suite.py --config configs/agent_suite/smoke.yaml --real
```
