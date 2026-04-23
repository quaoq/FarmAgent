from quao_scenario import evaluate
from rsare.agents.llm.deepseek_client import DeepSeekClient
from rsare.agents.agent.agent import Agent
from rsare.engine.engine import Engine
from rsare.scenarios.scenario.workflow import Workflow
from rsare.scenarios.scenario_farm_world.Contants import DETAILED_BRIEFING
from rsare.scenarios.scenario_farm_world.scenario_drone_survey import ScenarioFarmWorldDroneSurvey
from rsare.scenarios.scenario_farm_world.scenario_fertilizer import ScenarioFarmWorldFertilizer

from rsare.scenarios.scenario_farm_world.scenario_field_prep import ScenarioFarmWorldFieldPrep
from rsare.scenarios.scenario_farm_world.scenario_field_prep_planting import ScenarioFarmWorldFieldPrepPlanting
from rsare.scenarios.scenario_farm_world.scenario_irrigation import ScenarioFarmWorldIrrigation
from rsare.scenarios.scenario_farm_world.scenario_pesticide import ScenarioFarmWorldPesticide
from rsare.scenarios.scenario_farm_world.scenario_pesticide_outbreak import ScenarioFarmWorldPesticideOutbreak
from rsare.scenarios.scenario_farm_world.scenario_planting import ScenarioFarmWorldPlanting


def main():

    # llm = OpenAILLM(model="gpt-4o-mini", temperature=0.1)
    llm = DeepSeekClient(model="deepseek", temperature=1.0)


    scenario = ScenarioFarmWorldFieldPrepPlanting()
    if scenario.workflow is None:
        scenario.workflow = Workflow()

    # initiate_scenario populates scenario.apps with shared app instances
    scenario.initiate_scenario()

    agent = Agent(
        name="farm_agent",
        llm=llm,
        system_message=(
            "你是一个智能农场管理助手，负责协调农场的各种设备和操作。"
            "你需要根据天气、土壤状况等信息，合理安排农场作业。"
            "请按照农艺流程的正确顺序完成任务。"
        ),
        toolsets=scenario.apps,
    )

    engine = Engine(agent, scenario)

    engine.run_scenario_oracle()
    # oracle_workflow = Workflow.load_workflow(f"workflow_oracle_{scenario.scenario_id}_{DETAILED_BRIEFING}.json")
    engine.scenario.workflow.save_workflow(f"0421workflow_oracle_{scenario.scenario_id}_{DETAILED_BRIEFING}.json")

    # initiate_scenario populates scenario.apps with shared app instances
    # reset the scenario to clear any state changes from the oracle run before running the agent
    scenario.apps = None
    scenario.initiate_scenario()

    agent = Agent(
        name="farm_agent",
        llm=llm,
        system_message=(
            "你是一个智能农场管理助手，负责协调农场的各种设备和操作。"
            "你需要根据天气、土壤状况等信息，合理安排农场作业。"
            "请按照农艺流程的正确顺序完成任务。"
        ),
        toolsets=scenario.apps,
    )
    engine = Engine(agent, scenario)

    engine.run_scenario_agent()
    engine.agent.workflow.save_workflow(f"0421workflow_agent_{scenario.scenario_id}_{DETAILED_BRIEFING}.json")
    #
    oracle_workflow = engine.scenario.workflow
    agent_workflow = engine.agent.workflow
    # #
    result = evaluate(oracle_workflow, agent_workflow)
    print(f"\nFinal Result: {result}", flush=True)



if __name__ == "__main__":
    main()
