SCENARIO_INPUT = """Using Sentinel-1 GRD SAR imagery from the S1A and S1B satellites, covering the Shanghai region (121.0–123.0°E, 30.0–32.0°N) and the period from 2018-08-08 to 2018-08-10, load all available SAR scenes and clip a 500-m border buffer to remove edge artefacts.

Load global shoreline data and apply a 1-km shoreline buffer as a spatial mask to restrict each SAR scene to valid offshore analysis areas .

Detect vessels using the VH polarization band with a two-parameter CFAR configuration, applying a 200 × 200-pixel inner window and a 600 × 600-pixel outer window. Set the detection threshold to 16 for S1A scenes and 19 for S1B scenes.

For each CFAR detection, extract an 80 × 80-pixel dual-polarization (VH + VV) SAR tile. Apply a pre-trained neural network to confirm vessel presence, filter out false detections, and estimate vessel length.

Load environmental data (bathymetry, port distance, sea surface temperature, current speed, chlorophyll) and generate multiband raster stacks for fishing classification. Apply the fishing/non-fishing classifier to high-confidence vessel detections.

Finally, report the total number of detected vessel activities during the study period and the total number of vessels."""
from rsare.agents.agent.toolset_builder import agent_tool
from rsare.scenarios.scenario.scenario import Scenario
from rsare.scenarios.scenario.workflow import WorkflowStep


class Scenario3(Scenario):

    def __init__(self, scenario_id=None, scenario_input=None, sarTools=None):
        if scenario_id is None: scenario_id = 1
        if scenario_input is None: scenario_input = SCENARIO_INPUT
        super().__init__(scenario_id, scenario_input)
        self.sarTools = sarTools

    def initiate_scenario(self):
        pass

    def oracle_solution(self, run_oracle=False):
        date1 = '2018-08-08'
        date2 = '2018-08-10'
        region = [121.0, 30.0, 123.0, 32.0]

        # step 1
        args = {'date1': date1, 'date2': date2, 'region': region, 'satellite': 'S1AB',
                'collection': 'COPERNICUS/S1_GRD'}
        response = self.sarTools.load_SAR_scenes(**args)
        step1 = WorkflowStep(
            name="step1",
            op_type="WRITE",
            tool_name="load_SAR_scenes",
            tool_args=args,
            depends_on=[]
        )
        if run_oracle:
            self.workflow.add_node(step1)
            print(response)

        args2 = {'clip_buffer': 500.0}
        response2 = self.sarTools.clip_SAR_scenes(**args2)
        step2 = WorkflowStep(
            name="step2",
            op_type="WRITE",
            tool_name="clip_SAR_scenes",
            tool_args=args2,
            depends_on=["step1"]
        )
        if run_oracle:
            self.workflow.add_node(step2)
            print(response2)

        args3 = {'date1': date1, 'date2': date2, 'region': region}
        response3 = self.sarTools.load_global_shoreline_data(**args3)
        step3 = WorkflowStep(
            name="step3",
            op_type="READ",
            tool_name="load_global_shoreline_data",
            tool_args=args3,
            depends_on=[]
        )
        if run_oracle:
            self.workflow.add_node(step3)
            print(response3)

        args4 = {'shore_distance': 1000.0}
        response4 = self.sarTools.filter_shoreline_regions_sar_scenes(**args4)
        step4 = WorkflowStep(
            name="step4",
            op_type="WRITE",
            tool_name="filter_shoreline_regions_sar_scenes",
            tool_args=args4,
            depends_on=["step2", "step3"]
        )
        if run_oracle:
            self.workflow.add_node(step4)
            print(response4)

        args5 = {'inner_window_width': 200, 'inner_window_height': 200, 'outer_window_width': 600,
                 'outer_window_height': 600,
                 's1A_background_pixel_threshold': 18.0,
                 's1B_background_pixel_threshold': 18.0}
        response5 = self.sarTools.vessel_CFAR_detection(**args5)
        step5 = WorkflowStep(
            name="step5",
            op_type="WRITE",
            tool_name="vessel_CFAR_detection",
            tool_args=args5,
            depends_on=["step4"]
        )
        if run_oracle:
            self.workflow.add_node(step5)
            print(response5)

        args6 = {'tile_width': 80, 'tile_height': 80}
        response6 = self.sarTools.vessel_presence_length_estimation(**args6)
        step6 = WorkflowStep(
            name="step6",
            op_type="WRITE",
            tool_name="vessel_presence_length_estimation",
            tool_args=args6,
            depends_on=["step5"]
        )
        if run_oracle:
            self.workflow.add_node(step6)
            print(response6)

        args7 = {'date1': date1, 'date2': date2, 'region': region}
        if run_oracle:
            response7 = self.sarTools.load_bathymetry_data(**args7)
            response8 = self.sarTools.load_port_distance_data(**args7)
            response9 = self.sarTools.load_surface_temperature_data(**args7)
            response10 = self.sarTools.load_current_speed_data(**args7)
            response11 = self.sarTools.load_chlorophyll_data(**args7)
            response12 = self.sarTools.load_chlorophyll_data(**args7)
            print(response7)
            print(response8)
            print(response9)
            print(response10)
            print(response11)
            print(response12)

        step7 = WorkflowStep(
            name="step7",
            op_type="READ",
            tool_name="load_bathymetry_data",
            tool_args=args7,
            depends_on=[]
        )
        self.workflow.add_node(step7)

        step8 = WorkflowStep(
            name="step8",
            op_type="READ",
            tool_name="load_port_distance_data",
            tool_args=args7,
            depends_on=[])
        self.workflow.add_node(step8)

        step9 = WorkflowStep(
            name="step9",
            op_type="READ",
            tool_name="load_surface_temperature_data",
            tool_args=args7,
            depends_on=[]
        )
        self.workflow.add_node(step9)
        step10 = WorkflowStep(
            name="step10",
            op_type="READ",
            tool_name="load_current_speed_data",
            tool_args=args7,
            depends_on=[]
        )
        self.workflow.add_node(step10)
        step11 = WorkflowStep(
            name="step11",
            op_type="READ",
            tool_name="load_chlorophyll_data",
            tool_args=args7,
            depends_on=[]
        )
        self.workflow.add_node(step11)

        step12 = WorkflowStep(
            name="step12",
            op_type="READ",
            tool_name="load_AIS_data",
            tool_args=args7,
            depends_on=[]
        )
        self.workflow.add_node(step12)

        args13 = {'multiband_rasters': ["sar_cfar", "sar_vessel_length", "bathymetry",
                              "distance_from_port", "AIS_vessel_activity",
                              "surface_temperature", "current_speed", "chlorophyll"]}
        if run_oracle:
            response13 = self.sarTools.generate_multiband_raster_stacks(**args13)
            print(response13)
        step13 = WorkflowStep(
            name="step13",
            op_type="WRITE",
            tool_name="generate_multiband_raster_stacks",
            tool_args=args13,
            depends_on=["step6", "step7", "step8", "step9", "step10", "step11", "step12"]
        )
        self.workflow.add_node(step13)
        args14 = {'tile_width': 100,
            'tile_height':100,
            'multiband_rasters':["sar_cfar", "sar_vessel_length", "bathymetry",
                              "distance_from_port", "AIS_vessel_activity",
                              "surface_temperature", "current_speed", "chlorophyll"]}
        if run_oracle:
            response14 = self.sarTools.fishing_nonfishing_classification(**args14)
            print(response14)
        step14 = WorkflowStep(
            name="step14",
            op_type="WRITE",
            tool_name="fishing_nonfishing_classification",
            tool_args=args14,
            depends_on=["step13"]
        )
        self.workflow.add_node(step14)
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
    scenario = Scenario3(scenario_id=3, scenario_input={}, sarTools=sarTools)
    scenario.oracle_solution(run_oracle=True)
