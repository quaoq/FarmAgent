
from rsare.agents.llm.openai_llm import OpenAILLM
from rsare.agents.agent.agent import Agent
from rsare.engine.engine import Engine

from rsare.apps.gma.tools_list import SARTools
# from rsare.apps.gma.database import SARTools # just debugging testing
from rsare.scenarios.gma.scenario_1 import Scenario1
from rsare.scenarios.gma.scenario_0 import Scenario0


def main():

    # LLM
    llm = OpenAILLM(model="gpt-4o-mini", temperature=0.1)

    # Scenario APIs (tools)
    sarTools = SARTools()

    # Scenario to run
    scenario = Scenario1(sarTools=sarTools)

    # Agent
    agent = Agent(
        name="agent",
        llm=llm,
        system_message="You are a geospatial agent helping with fetching images from a database!",
        toolsets=[sarTools, scenario]
    )

    # Engine
    engine = Engine(agent, scenario)
    engine.run_scenario_oracle()
    engine.run_scenario_agent()


if __name__ == "__main__":
    main()
