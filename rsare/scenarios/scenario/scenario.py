# rsare/scenarios/scenario/scenario.py
import datetime
from typing import Any, Type, TypeVar, cast

from rsare.apps.farm_app import App
from rsare.engine.event import Event
from rsare.scenarios.scenario.workflow import Workflow

T = TypeVar("T", bound=App)


class Scenario:
    scenario_class: str = "base_scenario"
    scenario_id: str = ""
    scenario_input: str = ""
    dynamic_events: list | None = None
    start_time: float | None = None
    time_increment_in_seconds: int = 1
    apps: list[App] | None = None

    workflow: Workflow = None

    def __post_init__(self):
        if self.apps is None:
            self.apps = []
        if self.dynamic_events is None:
            self.dynamic_events = []
        if self.workflow is None:
            self.workflow = Workflow()


        # Copy the class's scenario_id to the instance if the instance's scenario_id is empty
        if not self.scenario_id and hasattr(self.__class__, "scenario_id"):
            self.scenario_id = getattr(self.__class__, "scenario_id")

    def init_and_populate_apps(self):
        """
        Logic that specifies the initial state for the ARE world
        This logic is scenario specific, implemented by subclasses
        """
        raise NotImplementedError(
            "initiate_scenario() must be implemented by subclasses.")

    def oracle_solution(self, run_oracle=False):
        """
        Logic that specifies the oracle solution for this task
        This logic is scenario specific, implemented by subclasses
        """
        raise NotImplementedError(
            "oracle_solution() must be implemented by subclasses.")

    def get_typed_app(self, app_type: Type[T], app_name: str | None = None) -> T:
        """
        Get the app with the given type and optional name.
        If name is not provided, it will be inferred from the app type.
        """
        name = app_name or app_type.__name__
        for app in self.apps or []:
            if isinstance(app, app_type) and app.name == name:
                return cast(T, app)
        raise ValueError(
            f"App {name} of type {app_type.__name__} not found in scenario."
        )

    def validate(self):

        return "Todo: implement scenario validation logic"
