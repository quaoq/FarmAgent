from rsare.agents.agent.argument_normalizer import normalize_tool_arguments
from rsare.agents.agent.toolset_builder import build_tool_schema
from rsare.scenarios.scenario_farm_world.scenario_irrigation import ScenarioFarmWorldIrrigation


def test_normalize_numeric_and_boolean_strings():
    schema = {
        "start": {"type": "integer"},
        "duration_hours": {"type": "number"},
        "enabled": {"type": "boolean"},
    }
    normalized = normalize_tool_arguments(
        tool_name="FieldOpsApp__irrigate_range",
        raw_arguments={"start": "22", "duration_hours": "1.5", "enabled": "true"},
        schema_properties=schema,
    )
    assert normalized == {"start": 22, "duration_hours": 1.5, "enabled": True}


def test_normalize_schema_dict_to_string():
    schema = {"content": {"type": "string"}}
    normalized = normalize_tool_arguments(
        tool_name="AgentUserInterface__send_message_to_user",
        raw_arguments={
            "content": {
                "description": "Irrigation completed successfully.",
                "type": "string",
                "default": "",
            }
        },
        schema_properties=schema,
    )
    assert normalized["content"] == "Irrigation completed successfully."


def test_normalize_invalid_integer_raises_clear_error():
    schema = {"start": {"type": "integer"}}
    try:
        normalize_tool_arguments(
            tool_name="FieldOpsApp__irrigate_range",
            raw_arguments={"start": "ridge-22"},
            schema_properties=schema,
        )
    except ValueError as error:
        assert "expected integer" in str(error)
    else:
        raise AssertionError("Expected ValueError for invalid integer coercion")


def test_irrigation_regression_string_arguments_no_longer_crash():
    scenario = ScenarioFarmWorldIrrigation()
    scenario.initiate_scenario()
    field_ops_app = next(app for app in scenario.apps if app.name == "FieldOpsApp")
    schema = {
        "start": {"type": "integer"},
        "end": {"type": "integer"},
        "duration_hours": {"type": "number"},
    }
    normalized = normalize_tool_arguments(
        tool_name="FieldOpsApp__irrigate_range",
        raw_arguments={"start": "22", "end": "32", "duration_hours": "1.5"},
        schema_properties=schema,
    )
    result = field_ops_app.irrigate_range(**normalized)
    assert result["status"] in {"irrigation_started", "ok"}


def test_build_tool_schema_handles_string_annotations():
    def sample_tool(start: "int", duration_hours: "float", message: "str") -> str:
        return f"{start}:{duration_hours}:{message}"

    schema = build_tool_schema(sample_tool)
    properties = schema["function"]["parameters"]["properties"]
    assert properties["start"]["type"] == "integer"
    assert properties["duration_hours"]["type"] == "number"
    assert properties["message"]["type"] == "string"
