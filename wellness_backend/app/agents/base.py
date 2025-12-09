from abc import ABC, abstractmethod
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq


class BaseAgent(ABC):
    """
    Base class for all agents.
    Every agent must:
    - read from state
    - write its own output back into state
    - return: {"next": <AgentName or None>, "state": state}
    """

    def __init__(self, llm: ChatGroq):
        self.llm = llm

    def _ask(self, system_prompt: str, human_prompt: str) -> str:
        """
        Standardized LLM call wrapper for agent prompts.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
        response = self.llm.invoke(messages)
        return response.content.strip()

    @abstractmethod
    def run(self, state: dict) -> dict:
        """
        Must return:
        {
            "next": "<NextAgentName or None>",
            "state": state
        }
        """
        ...
