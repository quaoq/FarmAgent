import time
from datetime import datetime

from rsare.engine.event import Event

SCENARIO_INPUT = """
Identify the regions with the highest and lowest densities of "publicly trackable vessel activities" in global ocean areas during August 2018.

Using Sentinel-1 GRD SAR imagery from the S1A and S1B satellites, covering the global ocean region and the period from 2018-08-01 to 2018-08-31, load all available SAR scenes and clip a 500-m border buffer to remove edge artefacts.

Detect vessels using the VH polarization band with a two-parameter CFAR configuration, applying a 200 × 200-pixel inner window and a 600 × 600-pixel outer window. Set the detection threshold to 16 for S1A scenes and 19 for S1B scenes.

For each CFAR detection, extract an 80 × 80-pixel dual-polarization (VH + VV) SAR tile. Apply a pre-trained neural network to confirm vessel presence, filter out false detections, and estimate vessel length.

Match detected vessels with AIS data to identify publicly trackable vessels. Load environmental data including bathymetry, port distances, surface temperature, current speed, and chlorophyll. Extract environmental tiles and apply fishing/non-fishing classification.

Aggregate detected vessels by grid cells with 0.1-degree resolution, normalize by overpasses, and identify the regions with highest and lowest densities of tracked vessel activities.
"""
from rsare.scenarios.scenario.scenario import Scenario
from rsare.scenarios.scenario.workflow import WorkflowStep


class EarthQuakeEvent(Event):
    def step(self):
        readable_time = datetime.fromtimestamp(self.time_start)
        return f"An earthquake has occurred at time {readable_time}!"


class ScenarioFigure1Task1(Scenario):

    def __init__(self, scenario_id=None, scenario_input=None, sarTools=None):

        if scenario_id is None:
            scenario_id = 5
        if scenario_input is None:
            scenario_input = SCENARIO_INPUT
        start_time = time.time()
        event = EarthQuakeEvent(time_start=start_time + 2, time_duration=30)
        super().__init__(scenario_id, scenario_input, dynamic_events=[event], start_time=start_time)
        self.sarTools = sarTools

    def initiate_scenario(self):
        pass

    def oracle_solution(self, run_oracle=True):
        date1 = '2018-08-01'
        date2 = '2018-08-31'
        region = [-180.0, -90.0, 180.0, 90.0]  # 全球范围

        # ========================================================================
        # 阶段A：加载SAR场景和CFAR检测
        # ========================================================================
        # step 1: load_SAR_scenes
        args1 = {'date1': date1, 'date2': date2, 'region': region, 'satellite': 'S1AB'}
        if run_oracle:
            response1 = self.sarTools.load_SAR_scenes(**args1)
            print(response1)
        step1 = WorkflowStep(
            name="step1",
            op_type="WRITE",
            tool_name="load_SAR_scenes",
            tool_args=args1,
            depends_on=[]
        )
        self.workflow.add_node(step1)

        # step 2: clip_SAR_scenes
        args2 = {'clip_buffer': 500.0}
        if run_oracle:
            response2 = self.sarTools.clip_SAR_scenes(**args2)
            print(response2)
        step2 = WorkflowStep(
            name="step2",
            op_type="WRITE",
            tool_name="clip_SAR_scenes",
            tool_args=args2,
            depends_on=["step1"]
        )
        self.workflow.add_node(step2)

        # step 3: vessel_CFAR_detection
        args3 = {
            'inner_window_width': 200,
            'inner_window_height': 200,
            'outer_window_width': 600,
            'outer_window_height': 600,
            's1A_background_pixel_threshold': 16.0,
            's1B_background_pixel_threshold': 19.0
        }
        if run_oracle:
            response3 = self.sarTools.vessel_CFAR_detection(**args3)
            print(response3)
        step3 = WorkflowStep(
            name="step3",
            op_type="WRITE",
            tool_name="vessel_CFAR_detection",
            tool_args=args3,
            depends_on=["step2"]
        )
        self.workflow.add_node(step3)

        # step 4: extract_vessel_detection_tiles
        args4 = {'tile_width': 80, 'tile_height': 80, 'tile_scale_m': 20.0}
        if run_oracle:
            response4 = self.sarTools.extract_vessel_detection_tiles(**args4)
            print(response4)
        step4 = WorkflowStep(
            name="step4",
            op_type="WRITE",
            tool_name="extract_vessel_detection_tiles",
            tool_args=args4,
            depends_on=["step3"]
        )
        self.workflow.add_node(step4)

        # ========================================================================
        # 阶段B：船舶长度和存在性预测
        # ========================================================================
        # step 5: vessel_presence_length_estimation
        args5 = {'tile_width': 80, 'tile_height': 80}
        if run_oracle:
            response5 = self.sarTools.vessel_presence_length_estimation(**args5)
            print(response5)
        step5 = WorkflowStep(
            name="step5",
            op_type="WRITE",
            tool_name="vessel_presence_length_estimation",
            tool_args=args5,
            depends_on=["step4"]
        )
        self.workflow.add_node(step5)

        # ========================================================================
        # 阶段C：AIS匹配
        # ========================================================================
        # step 6: load_AIS_data
        args6 = {'date1': date1, 'date2': date2, 'region': region}
        if run_oracle:
            response6 = self.sarTools.load_AIS_data(**args6)
            print(response6)
        step6 = WorkflowStep(
            name="step6",
            op_type="READ",
            tool_name="load_AIS_data",
            tool_args=args6,
            depends_on=["step5"]
        )
        self.workflow.add_node(step6)

        # step 7: sar_ais_matching
        args7 = {'matching_score_threshold': 7.4e-6}
        if run_oracle:
            response7 = self.sarTools.sar_ais_matching(**args7)
            print(response7)
        step7 = WorkflowStep(
            name="step7",
            op_type="WRITE",
            tool_name="sar_ais_matching",
            tool_args=args7,
            depends_on=["step6"]
        )
        self.workflow.add_node(step7)

        # ========================================================================
        # 阶段D：环境数据加载和捕鱼/非捕鱼分类
        # ========================================================================
        # step 8: load_bathymetry_data
        args8 = {'date1': date1, 'date2': date2, 'region': region}
        if run_oracle:
            response8 = self.sarTools.load_bathymetry_data(**args8)
            print(response8)
        step8 = WorkflowStep(
            name="step8",
            op_type="READ",
            tool_name="load_bathymetry_data",
            tool_args=args8,
            depends_on=["step7"]
        )
        self.workflow.add_node(step8)

        # step 9: load_port_distance_data
        args9 = {'date1': date1, 'date2': date2, 'region': region}
        if run_oracle:
            response9 = self.sarTools.load_port_distance_data(**args9)
            print(response9)
        step9 = WorkflowStep(
            name="step9",
            op_type="READ",
            tool_name="load_port_distance_data",
            tool_args=args9,
            depends_on=["step8"]
        )
        self.workflow.add_node(step9)

        # step 10: load_surface_temperature_data
        args10 = {'date1': date1, 'date2': date2, 'region': region}
        if run_oracle:
            response10 = self.sarTools.load_surface_temperature_data(**args10)
            print(response10)
        step10 = WorkflowStep(
            name="step10",
            op_type="READ",
            tool_name="load_surface_temperature_data",
            tool_args=args10,
            depends_on=["step9"]
        )
        self.workflow.add_node(step10)

        # step 11: load_current_speed_data
        args11 = {'date1': date1, 'date2': date2, 'region': region}
        if run_oracle:
            response11 = self.sarTools.load_current_speed_data(**args11)
            print(response11)
        step11 = WorkflowStep(
            name="step11",
            op_type="READ",
            tool_name="load_current_speed_data",
            tool_args=args11,
            depends_on=["step10"]
        )
        self.workflow.add_node(step11)

        # step 12: load_chlorophyll_data
        args12 = {'date1': date1, 'date2': date2, 'region': region}
        if run_oracle:
            response12 = self.sarTools.load_chlorophyll_data(**args12)
            print(response12)
        step12 = WorkflowStep(
            name="step12",
            op_type="READ",
            tool_name="load_chlorophyll_data",
            tool_args=args12,
            depends_on=["step11"]
        )
        self.workflow.add_node(step12)

        # step 13: generate_multiband_raster_stacks
        args13 = {}
        if run_oracle:
            response13 = self.sarTools.generate_multiband_raster_stacks(**args13)
            print(response13)
        step13 = WorkflowStep(
            name="step13",
            op_type="WRITE",
            tool_name="generate_multiband_raster_stacks",
            tool_args=args13,
            depends_on=["step12"]
        )
        self.workflow.add_node(step13)

        # step 14: extract_environmental_tiles
        args14 = {'tile_width': 100, 'tile_height': 100, 'presence_threshold': 0.7}
        if run_oracle:
            response14 = self.sarTools.extract_environmental_tiles(**args14)
            print(response14)
        step14 = WorkflowStep(
            name="step14",
            op_type="WRITE",
            tool_name="extract_environmental_tiles",
            tool_args=args14,
            depends_on=["step13"]
        )
        self.workflow.add_node(step14)

        # step 15: fishing_nonfishing_classification
        args15 = {'tile_width': 100, 'tile_height': 100, 'multiband_rasters': [
            "bathymetry",
            "port_distance",
            "surface_temperature",
            "current_speed",
            "chlorophyll"
        ]}
        if run_oracle:
            response15 = self.sarTools.fishing_nonfishing_classification(**args15)
            print(response15)
        step15 = WorkflowStep(
            name="step15",
            op_type="WRITE",
            tool_name="fishing_nonfishing_classification",
            tool_args=args15,
            depends_on=["step14"]
        )
        self.workflow.add_node(step15)

        # ========================================================================
        # 阶段F：网格聚合和密度计算
        # ========================================================================
        # step 16: aggregate_detections_by_grid
        args16 = {
            'date_start': date1,
            'date_end': date2,
            'scale_deg': 0.1,
            'activity_type': 'tracked',
            'normalize_by_overpasses': True
        }
        if run_oracle:
            response16 = self.sarTools.aggregate_detections_by_grid(**args16)
            print(response16)
        step16 = WorkflowStep(
            name="step16",
            op_type="WRITE",
            tool_name="aggregate_detections_by_grid",
            tool_args=args16,
            depends_on=["step15"]
        )
        self.workflow.add_node(step16)


if __name__ == "__main__":
    from rsare.apps.gma.tools_list import SARTools

    sarTools = SARTools()
    scenario = ScenarioFigure1Task1(scenario_id=5, scenario_input=None, sarTools=sarTools)
    scenario.oracle_solution()
