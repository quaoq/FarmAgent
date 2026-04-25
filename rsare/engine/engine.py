# rsare/engine/engine.py
import time
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
from threading import Thread

from rsare.apps.system import SystemApp
from rsare.scenarios.time_manager import TimeManager
from rsare.scenarios.scenario.workflow import WorkflowStep


class Engine:
    engine_name: str = "base_engine"

    def __init__(self, agent, scenario):
        """
        Initialize the Engine class.

        Args:
            agent (Agent): The agent class
            scenario (Scenario): The scenario class that defines the task.
            world (World): TODO: Separate the Class from the tool definitions
        """
        self.time_manager = TimeManager()
        self.start_time = scenario.start_time if scenario.start_time is not None else 0.0
        self.time_manager.reset(start_time=self.start_time)
        self.current_time = self.time_manager.time()

        self.agent = agent
        self.agent.set_time_manager(self.time_manager)

        self.scenario = scenario
        self._ensure_scenario_state()
        self._register_scenario_apps()

        self.time_increment_in_seconds = scenario.time_increment_in_seconds if scenario.time_increment_in_seconds is not None else 1

    def _register_scenario_apps(self):
        for app in self.scenario.apps or []:
            app.register_time_manager(self.time_manager)
            app.register_event_scheduler("engine", self.schedule_dynamic_event)
            if isinstance(app, SystemApp):
                app.wait_for_next_notification = self.wait_for_next_notification

    def _ensure_scenario_state(self):
        if self.scenario.apps is None:
            self.scenario.apps = []
        if self.scenario.dynamic_events is None:
            self.scenario.dynamic_events = []
        if self.scenario.workflow is None:
            from rsare.scenarios.scenario.workflow import Workflow

            self.scenario.workflow = Workflow()

    def schedule_dynamic_event(self, event):
        if self.scenario.dynamic_events is None:
            self.scenario.dynamic_events = []
        self.scenario.dynamic_events.append(event)

    def _next_dynamic_event(self):
        pending_events = [
            event for event in self.scenario.dynamic_events or [] if not event.triggered
        ]
        if not pending_events:
            return None
        return min(pending_events, key=lambda event: event.time_start)

    def _env_time_str(self):
        t = self.time_manager.time()
        return datetime.fromtimestamp(t, tz=CST).strftime("%Y-%m-%d %H:%M:%S")

    def _trigger_dynamic_event(self, event):
        self.current_time = self.time_manager.time()
        event.start(self.current_time)
        message = event.step()
        time_str = self._env_time_str()
        self.agent.messages.system_notify(message, time=time_str)
        self.agent.workflow.add_node(
            WorkflowStep(
                op_type="system",
                content=message,
                time=time_str,
            )
        )
        event.triggered = True

    def wait_for_next_notification(self):
        system_app = next(
            (
                app
                for app in self.scenario.apps or []
                if isinstance(app, SystemApp)
            ),
            None,
        )
        assert system_app is not None, "System app not found"
        wait_timeout = system_app.wait_for_notification_timeout
        assert wait_timeout is not None, "Wait for notification timeout not set"
        timeout_timestamp = wait_timeout.timeout_timestamp

        while True:
            self.current_time = self.time_manager.time()
            next_event = self._next_dynamic_event()
            next_event_time = next_event.time_start if next_event is not None else None

            if next_event_time is None or next_event_time > timeout_timestamp:
                jump_time = timeout_timestamp - self.time_manager.time()
                if jump_time > 0:
                    self.time_manager.add_offset(jump_time)
                system_app.reset_wait_for_notification_timeout()
                return

            jump_time = next_event_time - self.time_manager.time()
            if jump_time > 0:
                self.time_manager.add_offset(jump_time)
            self._trigger_dynamic_event(next_event)
            system_app.reset_wait_for_notification_timeout()
            return

    def run_scenario_agent(self):
        """
        Run the scenario
        """
        # Initiate the World state
        self.scenario.initiate_scenario()
        self._register_scenario_apps()
        # Run the agent against the task
        self.agent.run(input=self.scenario.scenario_input)
        print("=== Agent Workflow Solution ===")
        print(self.agent.workflow)

    def run_scenario_oracle(self, run_oracle=True):
        self._register_scenario_apps()
        self.scenario.oracle_solution(run_oracle=True)
        print("=== Oracle Workflow Solution ===")
        print(self.scenario.workflow)

    def run_scenario_dynamic(self):
        """
               Run the scenario
               """
        # Initiate the World state
        self.scenario.initiate_scenario()
        self._register_scenario_apps()

        # Run the agent against the
        def run_agent():
            self.agent.run(input=self.scenario.scenario_input)

        agent_thread = Thread(target=run_agent, name="Agent")
        agent_thread.daemon = True
        agent_thread.start()

        def _time_loop():
            while agent_thread.is_alive():
                self.current_time = self.time_manager.time()
                # Check for dynamic events to trigger
                for event in self.scenario.dynamic_events:
                    if not event.triggered and self.current_time >= event.time_start:
                        self._trigger_dynamic_event(event)
                time.sleep(1)
                self.time_manager.add_offset(self.time_increment_in_seconds - 1)

        time_thread = Thread(target=_time_loop, name="Time")
        time_thread.daemon = True
        time_thread.start()
