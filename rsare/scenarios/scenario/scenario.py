# rsare/scenarios/scenario/scenario.py
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

    workflow: Workflow | None = None

    def __init__(
        self,
        scenario_id: str | int | None = None,
        scenario_input: str | None = None,
        dynamic_events: list[Event] | None = None,
        start_time: float | None = None,
        time_increment_in_seconds: int | None = None,
        apps: list[App] | None = None,
    ) -> None:
        self.scenario_id = (
            str(scenario_id)
            if scenario_id is not None
            else str(getattr(self.__class__, "scenario_id", ""))
        )
        self.scenario_input = (
            str(scenario_input)
            if scenario_input is not None
            else str(getattr(self.__class__, "scenario_input", ""))
        )
        self.dynamic_events = list(dynamic_events) if dynamic_events is not None else []
        self.start_time = (
            start_time
            if start_time is not None
            else getattr(self.__class__, "start_time", None)
        )
        self.time_increment_in_seconds = (
            int(time_increment_in_seconds)
            if time_increment_in_seconds is not None
            else int(getattr(self.__class__, "time_increment_in_seconds", 1))
        )
        self.apps = list(apps) if apps is not None else []
        self.workflow = Workflow()

    def initiate_scenario(self):
        """
        Logic that specifies the initial state for the ARE world
        This logic is scenario specific, implemented by subclasses
        """
        raise NotImplementedError(
            "initiate_scenario() must be implemented by subclasses.")

    def init_and_populate_apps(self):
        self.initiate_scenario()

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
