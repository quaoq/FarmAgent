from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.scenario_0 import Scenario0
from rsare.scenarios.scenario_farm_world.scenario_field_prep import (
    ScenarioFarmWorldFieldPrep,
)
from rsare.scenarios.scenario_farm_world.scenario_harvest import (
    ScenarioFarmWorldHarvest,
)
from rsare.scenarios.scenario_farm_world.scenario_irrigation import (
    ScenarioFarmWorldIrrigation,
)
from rsare.scenarios.scenario_farm_world.scenario_pesticide import (
    ScenarioFarmWorldPesticide,
)


@dataclass(frozen=True)
class ScenarioRegistryItem:
    scenario_id: str
    domain: str
    builder: Callable[[], object]


def _build_gma_scenario_0() -> Scenario0:
    return Scenario0(sarTools=SARTools())


SCENARIO_REGISTRY: dict[str, ScenarioRegistryItem] = {
    "scenario_farm_world_field_prep": ScenarioRegistryItem(
        scenario_id="scenario_farm_world_field_prep",
        domain="farm",
        builder=ScenarioFarmWorldFieldPrep,
    ),
    "scenario_farm_world_irrigation": ScenarioRegistryItem(
        scenario_id="scenario_farm_world_irrigation",
        domain="farm",
        builder=ScenarioFarmWorldIrrigation,
    ),
    "scenario_farm_world_pesticide": ScenarioRegistryItem(
        scenario_id="scenario_farm_world_pesticide",
        domain="farm",
        builder=ScenarioFarmWorldPesticide,
    ),
    "scenario_farm_world_harvest": ScenarioRegistryItem(
        scenario_id="scenario_farm_world_harvest",
        domain="farm",
        builder=ScenarioFarmWorldHarvest,
    ),
    "scenario_gma_0": ScenarioRegistryItem(
        scenario_id="scenario_gma_0",
        domain="control",
        builder=_build_gma_scenario_0,
    ),
}


def list_registered_scenarios() -> list[str]:
    return sorted(SCENARIO_REGISTRY.keys())


def create_scenario(scenario_id: str):
    item = SCENARIO_REGISTRY.get(scenario_id)
    if item is None:
        raise ValueError(
            f"Unknown scenario_id '{scenario_id}'. Available: {list_registered_scenarios()}"
        )
    return item.builder()
