# rsare/scenarios/scenario/workflow.py

import json

class WorkflowStep:

    def __init__(self, 
            name = None,
            content = None,
            op_type = None,
            tool_name = None,
            tool_args = None,
            depends_on = [],
            time = None):
        """
        Initialize the base Workflow class.
        """
        self.name = name # node name "A", "B", ...
        self.content = content # tool or agent response
        self.op_type = op_type # READ or WRITE
        self.tool_name = tool_name # tool function if tool step
        self.tool_args = tool_args # Dict
        self.depends_on = depends_on # List (names of parent nodes)
        self.time = time

    def to_dict(self):
        return {
            "name": self.name,
            "content": self.content,
            "op_type": self.op_type,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "depends_on": self.depends_on,
            "time": self.time,
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

    @classmethod
    def load_workflow(cls, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        workflow = cls()

        # data is expected to be a dict: {step_name: step_dict, ...}
        for step_name, step_dict in data.items():
            # Ensure the internal name matches the key
            step_dict = dict(step_dict)  # shallow copy to avoid mutating original
            step_dict["name"] = step_name
            node = WorkflowStep(
                name=step_dict.get("name"),
                content=step_dict.get("content"),
                op_type=step_dict.get("op_type"),
                tool_name=step_dict.get("tool_name"),
                tool_args=step_dict.get("tool_args"),
                depends_on=step_dict.get("depends_on", []),
                time=step_dict.get("time"),
            )
            workflow.add_node(node)

        return workflow
