from rsare.agents.llm.openai_llm import OpenAILLM
from rsare.agents.agent.agent import Agent
from rsare.engine.engine import Engine

from rsare.apps.gma.tools_list import SARTools
# from rsare.apps.gma.database import SARTools # just debugging testing
from rsare.scenarios.gma.scenario_1 import Scenario1
from rsare.scenarios.gma.scenario_0 import Scenario0
from rsare.scenarios.gma.scenario_figure1_task1 import ScenarioFigure1Task1
from rsare.scenarios.scenario.workflow import Workflow
from rsare.validation.dfa_processor import generate_alphabet, generate_dfa, simplify_and_mark
from rsare.validation.metrics import path_correctness
from rsare.validation.utils.utils import extract_tool_names, parse_agent_output, fc2symbol


def main():
    # LLM
    llm = OpenAILLM(model="gpt-4o-mini", temperature=0.1)

    # Scenario APIs (tools)
    sarTools = SARTools()

    # Scenario to run
    scenario = ScenarioFigure1Task1(sarTools=sarTools)

    # Agent
    agent = Agent(
        name="agent",
        llm=llm,
        system_message="You are a geospatial agent helping with fetching images from a database!",
        toolsets=[sarTools, scenario]
    )

    # Engine
    engine = Engine(agent, scenario)
    #  add dynamic event
    engine.run_scenario_dynamic()
    engine.agent.workflow.save_workflow("workflow_agent.f1t1.json")

    engine.run_scenario_oracle()
    engine.scenario.workflow.save_workflow("workflow_oracle.f1t1.json")

    oracle_workflow = engine.scenario.workflow
    agent_workflow = engine.agent.workflow

    # oracle_workflow = Workflow.load_workflow("workflow_oracle.f1t1.json")
    # agent_workflow = Workflow.load_workflow("workflow_agent.f1t1.json")

    result = evaluate(oracle_workflow, agent_workflow, engine.agent.tool_schemas)
    print(f"Path Correctness: {result}", flush=True)


def evaluate(oracle_workflow: Workflow, agent_workflow: Workflow, tool_schemas) -> float:
    """
    Compute path correctness between oracle and agent workflows.

    Args:
        oracle_workflow: The oracle workflow
        agent_workflow: The agent workflow
    """
    tool_infos = extract_tool_names(tool_schemas)
    oracle_sequence = parse_agent_output(oracle_workflow.dag, tool_infos)
    agent_sequence = parse_agent_output(agent_workflow.dag, tool_infos)

    # symbol -> FunctionCall

    alphabet = generate_alphabet(oracle_sequence, tool_infos)
    dfa = generate_dfa(oracle_sequence, alphabet, tool_infos)

    print(dfa, flush=True)

    # convert agent sequence to symbols
    agent_symbols = [fc2symbol(fc, alphabet) for fc in agent_sequence]
    seq_symbols = [fc2symbol(fc, alphabet) for fc in oracle_sequence]
    print(f"Agent symbols: {agent_symbols}", flush=True)
    print(f"Expected symbols: {seq_symbols}", flush=True)

    simpl, mark, _ = simplify_and_mark(agent_symbols, dfa)
    distance = path_correctness(simpl, seq_symbols)
    return distance


if __name__ == "__main__":
    main()
