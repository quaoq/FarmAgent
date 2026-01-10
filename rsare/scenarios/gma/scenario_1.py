"""Using Sentinel-1 GRD SAR imagery from the S1A and S1B satellites, covering the Shanghai region (121.0–123.0°E, 30.0–32.0°N) and the period from 2018-08-08 to 2018-08-10, load all available SAR scenes and clip a 500-m border buffer to remove edge artefacts.

Load global shoreline data and apply a 1-km shoreline buffer as a spatial mask to restrict each SAR scene to valid offshore analysis areas .

Detect vessels using the VH polarization band with a two-parameter CFAR configuration, applying a 200 × 200-pixel inner window and a 600 × 600-pixel outer window. Set the detection threshold to 16 for S1A scenes and 19 for S1B scenes.

For each CFAR detection, extract an 80 × 80-pixel dual-polarization (VH + VV) SAR tile. Apply a pre-trained neural network to confirm vessel presence, filter out false detections, and estimate vessel length.

Finally, report the total number of detected vessel activities during the study period and the total number of vessels."""
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
        date1 = '2018-08-08'
        date2 = '2018-08-10'
        region = [121.0, 30.0, 123.0, 32.0]

        # step 1
        args = {'date1': date1, 'date2': date2, 'region': region, 'satellite': 'S1AB',
                'collection': 'COPERNICUS/S1_GRD'}
        response = self.sarTools.load_SAR_scenes(**args)
        step1 = FlowStep(
            name="step1",
            op_type="WRITE",
            tool_name="load_SAR_scenes",
            tool_args=args,
            depends_on=[]
        )
        self.flow.add_node(step1)
        print(response)

        args2 = {'clip_buffer': 500.0}
        response2 = self.sarTools.clip_SAR_scenes(**args2)
        step2 = FlowStep(
            name="step2",
            op_type="WRITE",
            tool_name="clip_SAR_scenes",
            tool_args=args2,
            depends_on=["step1"]
        )
        self.flow.add_node(step2)
        print(response2)

        args3 = {'date1': date1, 'date2': date2, 'region': region}
        response3 = self.sarTools.load_global_shoreline_data(**args3)
        step3 = FlowStep(
            name="step3",
            op_type="READ",
            tool_name="load_global_shoreline_data",
            tool_args=args3,
            depends_on=[]
        )
        self.flow.add_node(step3)
        print(response3)

        args4 = {'shore_distance': 1000.0}
        response4 = self.sarTools.filter_shoreline_regions_sar_scenes(**args4)
        step4 = FlowStep(
            name="step4",
            op_type="WRITE",
            tool_name="filter_shoreline_regions_sar_scenes",
            tool_args=args4,
            depends_on=["step2", "step3"]
        )
        self.flow.add_node(step4)
        print(response4)

        args5 = {'inner_window_width': 200, 'inner_window_height': 200, 'outer_window_width': 600,
                 'outer_window_height': 600,
                 's1A_background_pixel_threshold': 18.0,
                 's1B_background_pixel_threshold': 18.0}
        response5 = self.sarTools.vessel_CFAR_detection(**args5)
        step5 = FlowStep(
            name="step5",
            op_type="WRITE",
            tool_name="vessel_CFAR_detection",
            tool_args=args5,
            depends_on=["step4"]
        )
        self.flow.add_node(step5)
        print(response5)

        args6 = {'tile_width': 80, 'tile_height': 80}
        response6 = self.sarTools.vessel_presence_length_estimation(**args6)
        step6 = FlowStep(
            name="step6",
            op_type="WRITE",
            tool_name="vessel_presence_length_estimation",
            tool_args=args6,
            depends_on=["step5"]
        )
        self.flow.add_node(step6)
        print(response6)

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
    scenario = Scenario1(scenario_id=1, scenario_input={}, sarTools=sarTools)
    scenario.oracle_solution()
