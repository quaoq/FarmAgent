SCENARIO_INPUT = """
Using Sentinel-1 GRD SAR imagery from the S1A and S1B satellites over the Gulf of Mexico (-95.0, -94.0, 29.0, 30.0) for the period from 2019-01-01 to 2019-12-31, load all available SAR scenes.

Generate monthly SAR composites using a rolling 6-month median to suppress moving vessels and enhance stationary offshore objects.

Load global shoreline data and apply a 1-km shoreline buffer as a spatial mask to restrict each SAR scene to valid offshore analysis areas .

Detect stationary offshore infrastructure on the monthly median composites using a two-parameter CFAR configuration with a 140 × 140-pixel inner window and a 200 × 200-pixel outer window. Set the detection threshold to 16 for S1A scenes and 19 for S1B scenes.

Load Sentinel-2 optical scenes (RGB + NIR) from the S2A and S2B satellites .For each detected infrastructure candidate, generate 6-month SAR (VH + VV) composites and 6-month Sentinel-2 optical (RGB + NIR) composites . Extract 100 × 100-pixel multimodal tiles centred on each detected structure, and apply a pre-trained multimodal neural network to classify each structure as wind, oil, other, or noise.

Finally, report the total number of detected offshore structures and their spatial distribution.
"""
from rsare.agents.agent.toolset_builder import agent_tool
from rsare.scenarios.scenario.scenario import Scenario
from rsare.scenarios.scenario.workflow import WorkflowStep


class Scenario4(Scenario):

    def __init__(self, scenario_id=None, scenario_input=None, sarTools=None):
        if scenario_id is None: scenario_id = 1
        if scenario_input is None: scenario_input = SCENARIO_INPUT
        super().__init__(scenario_id, scenario_input)
        self.sarTools = sarTools

    def initiate_scenario(self):
        pass

    def oracle_solution(self, run_oracle=False):
        date1 = '2019-01-01'
        date2 = '2019-12-31'
        region = [-95.0, 29.0, -94.0, 30.0]

        # step 1
        args = {'date1': date1, 'date2': date2, 'region': region, 'satellite': 'S1AB',
                'collection': 'COPERNICUS/S1_GRD'}
        if run_oracle:
            response = self.sarTools.load_SAR_scenes(**args)
            print(response)
        step1 = WorkflowStep(
            name="step1",
            op_type="WRITE",
            tool_name="load_SAR_scenes",
            tool_args=args,
            depends_on=[]
        )
        self.workflow.add_node(step1)

        args2 = {'region': region,
                 'start_date': date1,
                 'tile_dx': 1,
                 'tile_dy': 1,
                 'time_window_duration': "6 months",
                 'satellite': "S1AB"}
        if run_oracle:
            response2 = self.sarTools.generate_median_scene_composites(**args2)
            print(response2)
        step2 = WorkflowStep(
            name="step2",
            op_type="WRITE",
            tool_name="generate_median_scene_composites",
            tool_args=args2,
            depends_on=["step1"]
        )
        self.workflow.add_node(step2)

        args3 = {'date1': date1, 'date2': date2, 'region': region}
        if run_oracle:
            response3 = self.sarTools.load_global_shoreline_data(**args3)
            print(response3)
        step3 = WorkflowStep(
            name="step3",
            op_type="READ",
            tool_name="load_global_shoreline_data",
            tool_args=args3,
            depends_on=[]
        )
        self.workflow.add_node(step3)

        args4 = {'shore_distance': 1000.0}
        if run_oracle:
            response4 = self.sarTools.filter_shoreline_regions_sar_scenes(**args4)
            print(response4)
        step4 = WorkflowStep(
            name="step4",
            op_type="WRITE",
            tool_name="filter_shoreline_regions_sar_scenes",
            tool_args=args4,
            depends_on=["step2", "step3"]
        )
        self.workflow.add_node(step4)

        args5 = {'inner_window_width': 140, 'inner_window_height': 140, 'outer_window_width': 200,
                 'outer_window_height': 200,
                 }
        if run_oracle:
            response5 = self.sarTools.infrastructure_CFAR_detection(**args5)
            print(response5)
        step5 = WorkflowStep(
            name="step5",
            op_type="WRITE",
            tool_name="infrastructure_CFAR_detection",
            tool_args=args5,
            depends_on=["step4"]
        )
        self.workflow.add_node(step5)

        args6 = {'date1': date1, 'date2': date2, 'region': region, 'satellite': 'S2AB',
                 'collection': 'COPERNICUS/S2'}
        if run_oracle:
            response = self.sarTools.load_optical_scenes(**args6)
            print(response)
        step6 = WorkflowStep(
            name="step6",
            op_type="WRITE",
            tool_name="load_optical_scenes",
            tool_args=args6,
            depends_on=[]
        )
        self.workflow.add_node(step6)

        args7 = {'time_window_duration': "6 months", 'multiband_image_bands': ["VH", "VV", "R", "G", "B", "NIR"], }
        if run_oracle:
            response = self.sarTools.generate_multiband_median_scene_composites(**args7)
            print(response)
        step7 = WorkflowStep(
            name="step7",
            op_type="WRITE",
            tool_name="generate_multiband_median_scene_composites",
            tool_args=args7,
            depends_on=["step5", "step6"]
        )
        self.workflow.add_node(step7)

        args8 = {'tile_width': 100,'tile_height': 100,'time_window_duration': "6 months",'multiband_image_bands': ["VH", "VV", "R", "G", "B", "NIR"] }
        if run_oracle:
            response = self.sarTools.infrastructure_classification(**args8)
            print(response)
        step8 = WorkflowStep(
            name="step8",
            op_type="WRITE",
            tool_name="infrastructure_classification",
            tool_args=args8,
            depends_on=["step7"]
        )
        self.workflow.add_node(step8)


@agent_tool
def check_loaded_images(self):
    """
    Check if SAR scenes are loaded

    Returns:
        Message confirming whether SAR scenes are loaded or not
    """
    return "SAR scenes are not loaded"


if __name__ == "__main__":
    from rsare.apps.gma.tools_list import SARTools

    sarTools = SARTools()
    sarTools.state.load_infra = True
    scenario = Scenario4(scenario_id=1, scenario_input={}, sarTools=sarTools)
    scenario.oracle_solution(run_oracle=True)
