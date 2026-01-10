# rsare/scenarios/scenario/workflow.py

class FlowStep:

    def __init__(self, 
            name,
            op_type = "WRITE",
            tool_name = None,
            tool_args = None,
            depends_on = []):
        """
        Initialize the base Workflow class.
        """
        self.name = name # node name "A", "B", ...
        self.op_type = op_type # READ or WRITE
        self.tool_name = tool_name # tool function if tool step
        self.tool_args = tool_args # Dict
        self.depends_on = depends_on # List (names of parent nodes)

class Workflow:

    workflow_class: str = "base_workflow"

    def __init__(self):
        """
        Initialize the base Workflow class.
        """
        self.dag = {}

    def add_node(self, node: FlowStep):
        self.dag[node.name] = node