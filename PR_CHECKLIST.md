# PR Checklist (FarmAgent)

Use this checklist when opening your PR.

## Scope

- [ ] Runtime blocker fixes (scenario init, tool schema, LLM import path)
- [ ] 10 research family suite (`rsare/research_suite/*`)
- [ ] A2A ON/OFF packs with typed experts
- [ ] Suite runner + readiness script
- [ ] Tool-argument normalization prevents int/string runtime crashes
- [ ] Docs: `AGENT_FAMILIES_AND_PAPERS.md`, `PROFESSOR_RUNBOOK.md`
- [ ] Dependency/repro setup (`pyproject.toml`, `requirements.txt`, `.env.example.professor`)

## Validation

- [ ] `uv run ./scripts/check_readiness.sh` passes
- [ ] `uv run python -m pytest tests -q` passes
- [ ] `uv run python scripts/run_agent_suite.py --config configs/agent_suite/smoke.yaml --mock` runs

## Notes for reviewers

- Focus review by subsystem:
  1) runtime fixes,
  2) research suite core,
  3) A2A wiring,
  4) docs/handoff.
- Release gate for handoff: readiness check + test suite + mock smoke artifacts.
