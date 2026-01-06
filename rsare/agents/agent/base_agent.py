# agents/agent/base_agent.py

import time
from rsare.agents.agent.messages import Messages

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
        self.messages = messages if messages is not None else Messages(provider=llm.provider)

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