# llm_clients/openai_client.py

from openai import OpenAI
from rsare.agents.llm.base_llm import BaseLLM
# from rsare.agents.modules.messages import ChatResponseMessage, ToolCall, ToolCallRequestMessage


class OpenAILLM(BaseLLM):
    llm_class: str = "OpenAILLM"

    def __init__(self, model, temperature=0.1, api_key=None, **kwargs):
        """
        Initialize the OpenAI client.

        Args:
            model (str): The model name (e.g., "gpt-4o-mini").
            api_key (str, optional): Your OpenAI API key.
            **kwargs: Additional parameters.
        """
        super().__init__(model, temperature, **kwargs)
        self.provider = "openai"
        self.api_key = api_key
        self.api_client = OpenAI()

    # Chat Completion API
    def chat_completion(self, messages, tools=None):
        """
        Send the conversation history (and tools, if provided) to
        OpenAI's API and return the response.

        Args:
            messages (list): Conversation history.
            tools (list, optional): Tool specifications.
        """
        response = self.api_client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=self.temperature,
        )
        return response

    def to_dict(self):
        return {
            'llm_class': self.llm_class,
            'model': self.model,
            'temperature': self.temperature
        }
