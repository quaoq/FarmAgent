# rsare/scenarios/scenario/scenario.py

from rsare.scenarios.scenario.workflow import Workflow

class Scenario:

    scenario_class: str = "base_scenario"

    def __init__(self, scenario_id, scenario_input):
        """
        Initialize the base Scenario class.

        Args:
            scenario_id (int): The id of the scenario defined.
            scenario_input (List[str]): The user prompt of the scenario defined.
                                        Support list of strings for multiround prompts.
        """
        self.scenario_id = scenario_id
        self.scenario_input = scenario_input
        self.workflow = Workflow()

    def initiate_scenario(self):
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

    def dynamic_events(self):
        """
        TODO: not sure if this will be either a separate function or 
            even standalone class
        """
        raise NotImplementedError(
            "dynamic_events() must be implemented by subclasses.")


