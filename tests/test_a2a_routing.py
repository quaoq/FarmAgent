from rsare.agents.agent.toolset_builder import agent_tool
from rsare.research_suite.a2a import apply_a2a_conversion


class WeatherApp:
    def __init__(self):
        self.name = "WeatherApp"

    @agent_tool()
    def read_weather(self):
        return {"ok": True}


class TractorApp:
    def __init__(self):
        self.name = "TractorApp"

    @agent_tool()
    def get_status(self):
        return {"fuel": 80}


def test_a2a_typed_expert_mapping_and_tool_wrap():
    weather = WeatherApp()
    tractor = TractorApp()
    telemetry = {}

    converted = apply_a2a_conversion(
        apps=[weather, tractor],
        enabled=True,
        app_prop=1.0,
        policy="typed_experts",
        fallback_app_agent="default_app_agent",
        telemetry=telemetry,
    )
    converted_by_type = {row["app_type"]: row["expert_agent"] for row in converted}
    assert converted_by_type["WeatherApp"] == "weather_expert_app_agent"
    assert converted_by_type["TractorApp"] == "machinery_expert_app_agent"

    _ = weather.read_weather()
    _ = tractor.get_status()
    assert telemetry["a2a_tool_calls"] == 2
