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

# KPOOL functions
from rsare.knowledge.utils import extract_pdf_text
from rsare.knowledge.rag.rag_pdf import RAG_PDF

# other packs
from pathlib import Path


SCENARIO_INPUT_RAG = """
Identify the regions with the highest and lowest densities of 
"publicly trackable vessel activities" in global ocean areas during August 2018 with S1A data.
Detect vessels via CFAR detection, and match with AIS data to identify publicly trackable vessels.

"""

SCENARIO_INPUT_RAG_PREFIX = """
You are given the following pointers. These are snippets from a technical report that details 
any steps required to carry out the aforementioned task. Please review and select the appropriate tools.

Hints:

"""


def main():

    # args
    outfile_oracle = "./workflows/workflow_oracle.f1t1.json"
        
    outfile_agent = "./workflows/workflow_agent.f1t1_RAG.json"
    rag_pdf = RAG_PDF(Path("./rsare/knowledge/rag/"))
    _RAG_INPUT = rag_pdf.rag_search(query=SCENARIO_INPUT_RAG, k = 10)
    SCENARIO_INPUT = SCENARIO_INPUT_RAG + SCENARIO_INPUT_RAG_PREFIX + _RAG_INPUT
    
    # LLM
    gpt_model = "gpt-5-nano" # "gpt-4o-mini"
    llm = OpenAILLM(model=gpt_model, temperature=0.1)

    # Scenario APIs (tools)
    sarTools = SARTools()

    # Scenario to run
    scenario = ScenarioFigure1Task1(sarTools=sarTools, scenario_input=SCENARIO_INPUT)

    # Agent
    agent = Agent(
        name="agent",
        llm=llm,
        system_message="You are a geospatial agent helping with fetching images from a database!",
        toolsets=[sarTools, scenario]
    )

    # Engine
    engine = Engine(agent, scenario)

    # engine.run_scenario_oracle()
    # engine.scenario.workflow.save_workflow(outfile_oracle)
    # oracle_workflow = engine.scenario.workflow
    
    engine.run_scenario_agent()
    engine.agent.workflow.save_workflow(outfile_agent)
    agent_workflow = engine.agent.workflow

    oracle_workflow = Workflow.load_workflow(outfile_oracle)
    agent_workflow = Workflow.load_workflow(outfile_agent)

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
