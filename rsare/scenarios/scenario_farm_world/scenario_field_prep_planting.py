from rsare.scenarios.scenario_farm_world.scenario_planting import (
    SCENARIO_INPUT,
    SCENARIO_INPUT_DETAIL,
    ScenarioFarmWorldPlanting,
)


class ScenarioFarmWorldFieldPrepPlanting(ScenarioFarmWorldPlanting):
    """
    Backward-compatible alias used by legacy scripts.

    This class keeps the historical scenario name while reusing the
    maintained planting implementation.
    """

    scenario_id: str = "scenario_farm_world_field_prep_planting"
    scenario_input: str = SCENARIO_INPUT_DETAIL
