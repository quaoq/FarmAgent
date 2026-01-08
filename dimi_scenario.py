
from rsare.agents.llm.openai_llm import OpenAILLM
from rsare.agents.agent.agent import Agent
from rsare.engine.engine import Engine

from rsare.apps.gma.database import SARTools
from rsare.scenarios.gma.scenario_1 import Scenario1

def main():

    # LLM
    llm = OpenAILLM(model="gpt-4o-mini", temperature=0.1)

    # Scenario APIs (tools)
    sarTools = SARTools()

    # Scenario to run
    scenario_input = "Get Sentinel-1 SAR scenes from 2018-08-01 to 2018-08-10 over Shanghai (i.e., 121.0, 30.0, 123.0, 32.0)!"
    scenario = Scenario1(scenario_id=0, scenario_input=scenario_input, sarTools=sarTools)

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
