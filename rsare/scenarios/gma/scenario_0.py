SCENARIO_INPUT="""
Get Sentinel-1 SAR scenes from 2018-08-01 to 2018-08-10 over Shanghai (i.e., 121.0, 30.0, 123.0, 32.0)!
"""

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.scenarios.scenario.scenario import Scenario
from rsare.scenarios.scenario.workflow import WorkflowStep


class Scenario0(Scenario):

    def __init__(self, scenario_id=None, scenario_input=None, sarTools=None):
        if scenario_id is None: scenario_id=0
        if scenario_input is None: scenario_input=SCENARIO_INPUT
        super().__init__(scenario_id, scenario_input)
        self.sarTools = sarTools

    def initiate_scenario(self):
        pass

    def oracle_solution(self, run_oracle=False):
        # step 1
        args = {'date1': '2018-08-08', 'date2': '2018-08-10', 'region': [121.0, 30.0, 123.0, 32.0], 'satellite': 'S1AB', 'collection': 'COPERNICUS/S1_GRD'}
        if run_oracle: 
            response = self.sarTools.load_SAR_scenes(**args)
            print(response)
        step1 = WorkflowStep(
            name="step1",
            op_type = "WRITE",
            tool_name = "load_SAR_scenes",
            tool_args = args,
            depends_on = []
        )
        self.workflow.add_node(step1)


    @agent_tool
    def check_loaded_images(self):
        """
        Check if SAR scenes are loaded

        Returns:
            Message confirming whether SAR scenes are loaded or not
        """
        return "SAR scenes are not loaded"