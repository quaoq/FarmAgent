import json
from rsare.agents.llm.openai_llm import OpenAILLM
from rsare.agents.agent.agent import Agent
from rsare.engine.engine import Engine

from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.scenario_figure1_task1 import ScenarioFigure1Task1
from rsare.scenarios.scenario.workflow import Workflow
from rsare.validation.metrics import LD, ktc


def _normalize_value(v):
    """Normalize a value for comparison: int/float unification, recursive for lists/dicts."""
    if isinstance(v, float) and v == int(v):
        return int(v)
    if isinstance(v, list):
        return tuple(_normalize_value(x) for x in v)
    if isinstance(v, dict):
        return tuple(sorted((k, _normalize_value(val)) for k, val in v.items()))
    return v


def _make_key(tool_name: str, tool_args: dict | None) -> tuple:
    if not tool_args:
        return (tool_name,)
    normalized = tuple(sorted((k, _normalize_value(v)) for k, v in tool_args.items()))
    return (tool_name, normalized)


def _format_args(tool_args: dict | None) -> str:
    if not tool_args:
        return ""
    return ", ".join(f"{k}={v}" for k, v in tool_args.items())


def _extract_tool_steps(dag) -> list[dict]:
    steps = dag.values() if isinstance(dag, dict) else dag
    result = []
    for step in steps:
        if isinstance(step, dict):
            if step.get("tool_name") and step.get("op_type") != "USER":
                result.append(step)
        else:
            tool_name = getattr(step, "tool_name", None)
            op_type = getattr(step, "op_type", None)
            if tool_name and op_type != "USER":
                args = getattr(step, "tool_args", {}) or {}
                result.append({"tool_name": tool_name, "tool_args": args})
    return result


def evaluate(oracle_workflow, agent_workflow, tool_schemas=None) -> dict:
    oracle_dag = oracle_workflow.dag if hasattr(oracle_workflow, "dag") else oracle_workflow
    agent_dag = agent_workflow.dag if hasattr(agent_workflow, "dag") else agent_workflow

    oracle_steps = _extract_tool_steps(oracle_dag)
    agent_steps = _extract_tool_steps(agent_dag)

    alphabet = {}
    next_letter_idx = 0

    def _get_symbol(tool_name, tool_args):
        nonlocal next_letter_idx
        key = _make_key(tool_name, tool_args)
        if key not in alphabet:
            if next_letter_idx < 26:
                sym = chr(ord("A") + next_letter_idx)
            else:
                sym = "A" + chr(ord("A") + (next_letter_idx - 26))
            alphabet[key] = {
                "symbol": sym,
                "tool_name": tool_name,
                "tool_args": tool_args,
            }
            next_letter_idx += 1
        return alphabet[key]["symbol"]

    oracle_symbols = [_get_symbol(s["tool_name"], s.get("tool_args")) for s in oracle_steps]
    agent_symbols = [_get_symbol(s["tool_name"], s.get("tool_args")) for s in agent_steps]

    print("\n=== Alphabet ===", flush=True)
    for entry in alphabet.values():
        args_str = _format_args(entry["tool_args"])
        label = f"{entry['tool_name']}({args_str})" if args_str else entry["tool_name"]
        print(f"  {entry['symbol']}: {label}", flush=True)

    print(f"\nOracle  ({len(oracle_symbols)}): {oracle_symbols}", flush=True)
    print(f"Agent   ({len(agent_symbols)}): {agent_symbols}", flush=True)

    # --- Path Correctness: 1 - LD/max(len_a, len_b) ---
    ld = LD(agent_symbols, oracle_symbols)
    max_len = max(len(agent_symbols), len(oracle_symbols), 1)
    pc = 1.0 - ld / max_len

    # --- KTC with coverage penalty ---
    oracle_set = set(oracle_symbols)
    ktc_val, matched = ktc(agent_symbols, oracle_symbols)
    coverage = len(matched) / len(oracle_set) if oracle_set else 0.0
    ktc_adjusted = ktc_val * coverage

    # --- Combined score ---
    score = 0.5 * pc + 0.5 * ktc_adjusted

    print(f"\nLevenshtein Distance: {ld}", flush=True)
    print(f"Path Correctness:    {pc:.4f}  (1 - {ld}/{max_len})", flush=True)
    print(f"KTC raw:             {ktc_val:.4f}  matched={matched}", flush=True)
    print(f"Coverage:            {coverage:.4f}  ({len(matched)}/{len(oracle_set)} unique oracle symbols)", flush=True)
    print(f"KTC adjusted:        {ktc_adjusted:.4f}  (ktc * coverage)", flush=True)
    print(f"Combined Score:      {score:.4f}", flush=True)

    return {
        "path_correctness": round(pc, 4),
        "ktc_raw": round(ktc_val, 4),
        "coverage": round(coverage, 4),
        "ktc_adjusted": round(ktc_adjusted, 4),
        "combined": round(score, 4),
    }


def main():
    llm = OpenAILLM(model="gpt-4o-mini", temperature=0.1)
    sarTools = SARTools()
    scenario = ScenarioFigure1Task1(sarTools=sarTools)

    agent = Agent(
        name="agent",
        llm=llm,
        system_message="You are a geospatial agent helping with fetching images from a database!",
        toolsets=[sarTools, scenario]
    )

    engine = Engine(agent, scenario)
    engine.run_scenario_dynamic()
    engine.agent.workflow.save_workflow("workflow_agent.f1t1.json")

    engine.run_scenario_oracle()
    engine.scenario.workflow.save_workflow("workflow_oracle.f1t1.json")

    result = evaluate(engine.scenario.workflow, engine.agent.workflow)
    print(f"\nResult: {result}", flush=True)


if __name__ == "__main__":
    main()
