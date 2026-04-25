# agents/agent/base_agent.py

import time
from datetime import datetime, timezone, timedelta
from rsare.agents.agent.messages import Messages
from rsare.scenarios.scenario.workflow import Workflow, WorkflowStep

# Beijing timezone (UTC+8)
CST = timezone(timedelta(hours=8))

class BaseAgent:
    def __init__(self, name, llm, system_message=None, messages=None):
        """
        Minimal BaseAgent which holds basic parameters.
        
        Args:
            name (str): The agent's name.
            llm: An LLM client instance.
            tools (list, optional): List of tool functions available.
            system_message (str, optional): Instructional system message.
        """
        self.name = name
        self.llm = llm
        self.system_message = system_message
        self.messages = messages if messages is not None else Messages(provider=llm.provider, system_message=system_message)
        self.time_manager = None
        self.workflow = Workflow()

    def log(self, message):
        print(f"[{self.name}] {message}")

    def chat_completion(self, messages, tools=None):
        """
        Given a conversation history (messages) and an optional list of tools,
        return a response from the language model.

        Args:
            messages (list): A list of message dictionaries representing the conversation history.
            tools (list, optional): A list of tool specifications available for function calling.

        Returns:
            dict: A dictionary containing the model's response, input tokens, output tokens, etc.
        """
        start_time = time.time()
        response = self.llm.chat_completion(messages, tools)
        elapsed_time = round(time.time() - start_time, 4)
        self.messages.llm_response(response, elapsed_time)
        return response.choices[0].message

    def env_time_str(self):
        if self.time_manager:
            t = self.time_manager.time()
            return datetime.fromtimestamp(t, tz=CST).strftime("%Y-%m-%d %H:%M:%S")
        return None

    def set_time_manager(self, time_manager):
        self.time_manager = time_manager