# rsare/scenarios/scenario/workflow.py

import json

class WorkflowStep:

    def __init__(self, 
            name = None,
            content = None,
            op_type = None,
            tool_name = None,
            tool_args = None,
            depends_on = []):
        """
        Initialize the base Workflow class.
        """
        self.name = name # node name "A", "B", ...
        self.content = content # tool or agent response
        self.op_type = op_type # READ or WRITE
        self.tool_name = tool_name # tool function if tool step
        self.tool_args = tool_args # Dict
        self.depends_on = depends_on # List (names of parent nodes)

    def to_dict(self):
        return {
            "name": self.name,
            "content": self.content,
            "op_type": self.op_type,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "depends_on": self.depends_on,
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=2)

class Workflow:

    workflow_class: str = "base_workflow"

    def __init__(self):
        """
        Initialize the base Workflow class.
        """
        self.dag = {}

    def __len__(self):
        return len(self.dag)

    
    def to_dict(self):
        return {
            step_name: step.to_dict()
            for step_name, step in self.dag.items()
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=2)

    def add_node(self, node: WorkflowStep):
        name = node.name if node.name else f"step{len(self.dag)}"
        self.dag[name] = node

    def save_workflow(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
