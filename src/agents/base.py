"""
Base Agent implementation for SED Agentic Orchestration Layer.
"""
from typing import List, Dict, Any, Optional, Callable
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class AgentContext:
    """Context passed between agents."""
    trace_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseAgent:
    """
    Base class for all agents in the orchestration layer.
    """
    
    def __init__(
        self, 
        name: str, 
        role: str,
        system_prompt: str,
        model: str = "qwen2:1.5b",
        tools: Optional[List[Callable]] = None
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.tools = tools or []
        self.logger = logging.getLogger(f"agent.{name}")

    def run(self, message: str, context: Optional[AgentContext] = None) -> str:
        """
        Main entry point for agent execution.
        
        Args:
            message: The user's input or task description.
            context: Contextual information for the execution.
            
        Returns:
            The agent's response or result.
        """
        self.logger.info(f"Agent {self.name} received message: {message}")
        
        # TODO: Integrate with actual LLM backend (Ollama/OpenAI) 
        # For now, we'll simulate the thinking process and return a placeholder or 
        # allow subclasses to override this method completely.
        
        response = self._think(message, context)
        return response

    def _think(self, message: str, context: Optional[AgentContext]) -> str:
        """
        Internal reasoning loop.
        Can be overridden by subclasses or implemented with a ReAct loop here.
        """
        # Placeholder for actual LLM call and tool usage logic
        return f"[{self.name}] Processed: {message}"

    def _call_llm(self, prompt: str) -> str:
        """Helper to call the configured LLM."""
        # This acts as a wrapper around logic similar to LocalLogAnalyzer._create_prompt + client.chat
        # For the foundation step, we might just use the existing LocalLogAnalyzer logic or 
        # instantiate a pure Ollama client here.
        pass

    def add_tool(self, tool: Callable):
        """Register a new tool for the agent."""
        self.tools.append(tool)
