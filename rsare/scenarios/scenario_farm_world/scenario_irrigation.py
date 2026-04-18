from __future__ import annotations

from datetime import datetime, timezone

from rsare.apps.farm_world.drone_app import DroneApp
from rsare.apps.farm_world.farm_world_app import FarmWorldApp
from rsare.apps.farm_world.field_ops_app import FieldOpsApp
from rsare.apps.farm_world.robot_app import RobotApp
from rsare.apps.farm_world.sensor_app import SensorApp
from rsare.apps.farm_world.tractor_app import TractorApp
from rsare.apps.farm_world.weather_app import WeatherApp
from rsare.apps.system import SystemApp
from rsare.scenarios.scenario.scenario import Scenario
from rsare.scenarios.scenario.workflow import WorkflowStep
from rsare.scenarios.scenario_farm_world.Contants import DETAILED_BRIEFING

_DRY_START = 20
_DRY_END = 39
_IRRIGATION_HOURS = 1.5

SCENARIO_INPUT_DETAIL = """
作物已进入V2生长阶段（播种后约22天），最近持续干旱无雨。
请按以下步骤操作：
1. 查看今天天气。
2. 查看未来几天预报，如果近期有雨就不用灌溉了，让天然降雨补充水分。
3. 读取6个土壤传感器，找出VWC < 0.20的干旱区域（正常应在0.20-0.30之间）。
4. 用 Mavic3M 检查无人机电量。
5. 飞行巡查干旱区域，通过冠层温度和NDVI确认水分胁迫情况。
6. 对干旱区域灌溉1.5小时。灌溉会使土壤VWC增加约0.08。
7. 灌溉完成后再次读取传感器，确认土壤湿度已恢复到正常范围。
8. 向我汇报灌溉完成情况。
"""

SCENARIO_INPUT = """最近一直没下雨，地有点干了。查查哪些地方缺水，灌溉一下。完成后告诉我。"""


class ScenarioFarmWorldIrrigation(Scenario):
    """
    Mid-season irrigation decision-making.

    Crops are at V2-V3 stage. A dry spell has left ridges 20-39 with low
    soil moisture. The agent must identify the dry zone via sensors and
    drone survey, check the forecast (no rain coming), then irrigate the
    affected ridges. After irrigation, re-read sensors to confirm.
    """

    scenario_id: str = "scenario_farm_world_irrigation"
    scenario_input: str = SCENARIO_INPUT_DETAIL if DETAILED_BRIEFING else SCENARIO_INPUT
    start_time: float | None = (
        datetime(2026, 5, 20, 7, 0, 0, tzinfo=timezone.utc).timestamp() - 8 * 3600
    )
    time_increment_in_seconds: int = 60

    def initiate_scenario(self):
        if self.apps:
            return
        farm_world = FarmWorldApp()
        weather = WeatherApp()
        sensor = SensorApp(farm_world_app=farm_world)
        mavic = DroneApp(
            farm_world_app=farm_world,
            weather_app=weather,
            name="Mavic3M",
            description="DJI Mavic 3 Multispectral — multispectral imaging drone for NDVI vegetation index mapping",
            speed_ms=5.0,
            effective_ridges_per_pass=7,
            battery_pct_per_ridge=1.0,
        )
        matrice = DroneApp(
            farm_world_app=farm_world,
            weather_app=weather,
            name="Matrice4T",
            description="DJI Matrice 4T — thermal imaging drone for canopy temperature and stress detection",
            speed_ms=4.0,
            effective_ridges_per_pass=5,
            battery_pct_per_ridge=1.5,
        )
        robot_0 = RobotApp(
            farm_world_app=farm_world,
            weather_app=weather,
            name="Robot0",
            description="Zhiyuan D1 Max #1 — ground-level pest/disease inspection robot",
        )
        robot_1 = RobotApp(
            farm_world_app=farm_world,
            weather_app=weather,
            name="Robot1",
            description="Zhiyuan D1 Max #2 — ground-level pest/disease inspection robot",
        )
        tractor = TractorApp(farm_world_app=farm_world, weather_app=weather)
        field_ops = FieldOpsApp(farm_world_app=farm_world, weather_app=weather)
        system = SystemApp()

        self.apps = [
            farm_world, weather, sensor, mavic, matrice,
            robot_0, robot_1, tractor, field_ops, system,
        ]

        # --- Configure initial state ---
        weather.set_weather(
            date="2026-05-20",
            temp_c=26.0,
            humidity_pct=35.0,
            wind_speed_ms=1.5,
            rainfall_mm=0.0,
            solar_radiation=550.0,
            forecast=[
                {"date": "2026-05-21", "temp_c": 27.0, "humidity_pct": 30.0,
                 "wind_speed_ms": 2.0, "rainfall_mm": 0.0, "solar_radiation": 560.0},
                {"date": "2026-05-22", "temp_c": 28.0, "humidity_pct": 28.0,
                 "wind_speed_ms": 1.0, "rainfall_mm": 0.0, "solar_radiation": 570.0},
                {"date": "2026-05-23", "temp_c": 25.0, "humidity_pct": 40.0,
                 "wind_speed_ms": 3.0, "rainfall_mm": 0.0, "solar_radiation": 500.0},
            ],
            avg_soil_vwc=0.19,
        )
        farm_world.set_season_phase("growing")

        for i in range(64):
            r = farm_world.get_ridge(i)
            r.planted = True
            r.seed_type = "STANDARD"
            r.days_since_planted = 22
            r.growth_stage = "V2"
            r.soil_temp_c = 18.0 + (i % 3) * 0.5
            if _DRY_START <= i <= _DRY_END:
                r.soil_vwc = 0.14 + (i % 3) * 0.01
            else:
                r.soil_vwc = 0.22 + (i % 4) * 0.01

    def oracle_solution(self, run_oracle=False):
        weather = self.get_typed_app(WeatherApp)
        sensor = self.get_typed_app(SensorApp)
        field_ops = self.get_typed_app(FieldOpsApp)
        mavic = self.get_typed_app(DroneApp, app_name="Mavic3M")

        if run_oracle:
            print(weather.get_current_weather())
        self.workflow.add_node(WorkflowStep(
            name="check_weather", op_type="READ",
            tool_name="get_current_weather", tool_args={}, depends_on=[],
        ))

        if run_oracle:
            print(weather.get_forecast(days=3))
        self.workflow.add_node(WorkflowStep(
            name="check_forecast", op_type="READ",
            tool_name="get_forecast", tool_args={"days": 3},
            depends_on=["check_weather"],
        ))

        if run_oracle:
            print(sensor.read_soil_sensors())
        self.workflow.add_node(WorkflowStep(
            name="read_soil", op_type="READ",
            tool_name="read_soil_sensors", tool_args={},
            depends_on=["check_forecast"],
        ))

        if run_oracle:
            print(mavic.check_status())
        self.workflow.add_node(WorkflowStep(
            name="check_drone", op_type="READ",
            tool_name="check_status", tool_args={},
            depends_on=["read_soil"],
        ))

        if run_oracle:
            print(mavic.fly_survey(22, 43))
        self.workflow.add_node(WorkflowStep(
            name="survey_dry_zone", op_type="READ",
            tool_name="fly_survey",
            tool_args={"start_ridge": 22, "end_ridge": 43},
            depends_on=["check_drone"],
        ))

        if run_oracle:
            print(field_ops.irrigate_range(_DRY_START, _DRY_END, _IRRIGATION_HOURS))
        self.workflow.add_node(WorkflowStep(
            name="irrigate", op_type="WRITE",
            tool_name="irrigate_range",
            tool_args={"start_ridge": _DRY_START, "end_ridge": _DRY_END,
                        "hours": _IRRIGATION_HOURS},
            depends_on=["survey_dry_zone"],
        ))

        if run_oracle:
            print(sensor.read_soil_sensors())
        self.workflow.add_node(WorkflowStep(
            name="verify_soil", op_type="READ",
            tool_name="read_soil_sensors", tool_args={},
            depends_on=["irrigate"],
        ))
