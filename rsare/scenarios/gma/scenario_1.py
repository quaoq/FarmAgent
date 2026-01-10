
from rsare.agents.agent.toolset_builder import agent_tool
from rsare.scenarios.scenario.scenario import Scenario
from rsare.scenarios.scenario.workflow import Workflow
from rsare.scenarios.scenario.workflow import FlowStep


class Scenario1(Scenario):

    def __init__(self, scenario_id, scenario_input, sarTools):
        super().__init__(scenario_id, scenario_input)
        self.sarTools = sarTools
        self.flow = Workflow()

    def initiate_scenario(self):
        pass

    def oracle_solution(self):
        # step 1
        args = {'date1': '2018-08-08', 'date2': '2018-08-10', 'region': [121.0, 30.0, 123.0, 32.0], 'satellite': 'S1AB', 'collection': 'COPERNICUS/S1_GRD'}
        response = self.sarTools.load_SAR_scenes(**args)
        step1 = FlowStep(
            name="step1",
            op_type = "WRITE",
            tool_name = "load_SAR_scenes",
            tool_args = args,
            depends_on = []
        )
        self.flow.add_node(step1)
        print(response)



    @agent_tool
    def check_loaded_images(self):
        """
        Check if SAR scenes are loaded

        Returns:
            Message confirming whether SAR scenes are loaded or not
        """
        return "SAR scenes are not loaded"