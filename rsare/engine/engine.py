# rsare/engine/engine.py


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
        self.agent = agent
        self.scenario = scenario

    def run_scenario_agent(self):
        """
        Run the scenario
        """
        # Initiate the World state
        self.scenario.initiate_scenario()
        # Run the agent against the task
        self.agent.run(input=self.scenario.scenario_input)

    def run_scenario_oracle(self):
        self.scenario.oracle_solution()

    def run_scenario_dynamic(self):
        raise NotImplementedError(
            "TODO: run_scenario_dynamic() implemented later when adding dynamic logic!")
