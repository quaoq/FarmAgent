# agents/agent/agent.py

import time
import json
import re
from pathlib import Path
from collections import deque, OrderedDict

from rsare.agents.agent.base_agent import BaseAgent
from rsare.agents.agent.toolset_builder import build_toolset


class Agent(BaseAgent):

    def __init__(self, name, llm, system_message="", messages=None, toolsets=None):
        """
        Agent extends BaseAgent with function-calling logic.
        
        Args:
            name (str): The agent's name.
            model_client: An instance of an LLM client.
            system_message (str, optional): A system instruction message.
            messages (optional): A Messages instance holding the conversation history.
            toolsets (list, optional): A list of Class objects (e.g., database API) from which agent tools are extracted.
        """
        super().__init__(name, llm, system_message, messages)
        self.tools=None
        self.tool_schemas=None
        self.tools_map=None
        if toolsets is not None:
            self.tools, self.tool_schemas, self.tools_map = \
                build_toolset(toolsets)

    def call_function(self, tool_call):
        
        name = tool_call.function.name
        tool_call_id=tool_call.id
        args = json.loads(tool_call.function.arguments)
        self.log(f"Calling tool: {name}({args})")
        tool_type=tool_call.type

        # Call corresponding function with provided arguments
        start_time = time.time()
        tool_response = self.tools_map[name](**args)
        elapsed_time = round(time.time() - start_time, 4)
        self.messages.tool_call_response(tool_response, tool_call, elapsed_time)
        
    def run(self, input):
        """
        Add the user input to the conversation history, then call chat_completion()
        """
        self.messages.user_input(input)

        while True:

            message = self.chat_completion(self.messages(), tools=self.tool_schemas)
            if not message.tool_calls: # if finished handling tool calls, break
                break

            # === handle tool calls ===
            for tool_call in message.tool_calls:
                self.call_function(tool_call)

        return message.content
