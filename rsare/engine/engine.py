# rsare/engine/engine.py
import time
from threading import Thread

from rsare.scenarios.time_manager import TimeManager


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

        self.time_increment_in_seconds = scenario.time_increment_in_seconds if scenario.time_increment_in_seconds is not None else 1

    def run_scenario_agent(self):
        """
        Run the scenario
        """
        # Initiate the World state
        self.scenario.initiate_scenario()
        # Run the agent against the task
        self.agent.run(input=self.scenario.scenario_input)
        print("=== Agent Workflow Solution ===")
        print(self.agent.workflow)

    def run_scenario_oracle(self, run_oracle=True):
        self.scenario.oracle_solution(run_oracle=True)
        print("=== Oracle Workflow Solution ===")
        print(self.scenario.workflow)

    def run_scenario_dynamic(self):
        """
               Run the scenario
               """
        # Initiate the World state
        self.scenario.initiate_scenario()

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
                        event.start(self.current_time)
                        self.agent.messages.system_notify(event.step())
                        event.triggered = True
                time.sleep(1)
                self.time_manager.add_offset(self.time_increment_in_seconds - 1)

        time_thread = Thread(target=_time_loop, name="Time")
        time_thread.daemon = True
        time_thread.start()
