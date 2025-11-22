"""
Main deep-agent hospitality concierge setup.

Creates a deep-agent with:
- InMemoryStore backend for persistent guest memory
- TodoList middleware for planning multi-step tasks
- Filesystem middleware for context management
- SubAgent middleware with 3 specialized subagents
- Direct access to all activity and booking tools
"""

import logging
from typing import Any, Dict, List, Optional

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain_openai import ChatOpenAI
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver

from backend.chatbot_core.config import Config

from .prompts import MAIN_CONCIERGE_PROMPT
from .subagents import get_subagent_configs
from .tools import ALL_TOOLS

logger = logging.getLogger(__name__)


class DeepAgentConcierge:
    """
    Deep-agent powered hospitality concierge.

    Manages the creation and configuration of the main concierge agent
    with specialized subagents for bookings, recommendations, and knowledge.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the deep-agent concierge.

        Args:
            model: Model name (defaults to Config.AI_MODEL)
            api_key: API key (defaults to Config.get_ai_api_key())
            base_url: Base URL for API (defaults to OpenRouter for unified access)
        """
        # Use configuration from existing Django settings
        self.model = model or Config.AI_MODEL
        self.api_key = api_key or Config.get_ai_api_key()
        self.base_url = base_url or "https://openrouter.ai/api/v1"

        # Initialize store for persistent memory
        self.store = InMemoryStore()

        # Initialize checkpointer for conversation persistence
        self.checkpointer = MemorySaver()

        # Create the agent
        self.agent = None
        self._create_agent()

        logger.info(
            f"DeepAgentConcierge initialized with model={self.model}, "
            f"base_url={self.base_url}"
        )

    def _make_backend(self, runtime):
        """
        Create composite backend with ephemeral and persistent storage.

        /workspace/ - Ephemeral files for current conversation (StateBackend)
        /memories/ - Persistent guest data across sessions (StoreBackend)

        Args:
            runtime: LangGraph runtime context

        Returns:
            CompositeBackend instance
        """
        return CompositeBackend(
            default=StateBackend(runtime),  # Ephemeral workspace
            routes={
                "/memories/": StoreBackend(runtime)  # Persistent memories
            },
        )

    def _create_langchain_model(self):
        """
        Create LangChain ChatOpenAI model configured for OpenRouter.

        Returns:
            ChatOpenAI instance
        """
        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.7,  # Balanced creativity
            max_tokens=1000,  # Concise responses for WhatsApp
            # OpenRouter-specific headers
            default_headers={
                "HTTP-Referer": "https://github.com/whatsapp-ai",
                "X-Title": "WhatsApp AI Hospitality Concierge",
            },
        )

    def _create_agent(self):
        """Create the main deep-agent with all middleware and tools."""
        try:
            # Create LangChain model
            model = self._create_langchain_model()

            # Get subagent configurations
            subagent_configs = get_subagent_configs()

            logger.info(
                f"Creating deep-agent with {len(subagent_configs)} subagents: "
                f"{[cfg['name'] for cfg in subagent_configs]}"
            )

            # Create deep-agent with auto-attached middleware
            # create_deep_agent automatically attaches:
            # - TodoListMiddleware (for planning)
            # - FilesystemMiddleware (for context management)
            # - SubAgentMiddleware (for task delegation)
            self.agent = create_deep_agent(
                model=model,
                system_prompt=MAIN_CONCIERGE_PROMPT,
                tools=ALL_TOOLS,  # Direct access to all tools
                store=self.store,  # Persistent memory store
                backend=self._make_backend,  # Composite backend function
                checkpointer=self.checkpointer,  # Conversation persistence
                # Subagent configuration
                subagents=subagent_configs,
            )

            logger.info("Deep-agent created successfully")

        except Exception as e:
            logger.error(f"Error creating deep-agent: {e}", exc_info=True)
            raise

    def process_message(
        self, user_phone: str, message_content: str
    ) -> Dict[str, Any]:
        """
        Process a message through the deep-agent.

        Args:
            user_phone: User's phone number (used as thread_id)
            message_content: The message content from the user

        Returns:
            Dictionary with:
                - success: bool
                - response: str (agent's response text)
                - metadata: dict (agent execution metadata)
                - error: str (if success=False)
        """
        try:
            logger.info(f"Processing message from {user_phone}: {message_content[:50]}...")

            # Configure with thread_id for conversation persistence
            config = {
                "configurable": {
                    "thread_id": f"guest-{user_phone}",
                    "user_phone": user_phone,  # Make available in runtime context
                }
            }

            # Invoke the agent
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": message_content}]},
                config,
            )

            # Extract response from the last message
            messages = result.get("messages", [])
            if not messages:
                logger.warning("Agent returned no messages")
                return {
                    "success": False,
                    "response": "",
                    "metadata": {},
                    "error": "Agent returned no response",
                }

            # Get the last assistant message
            last_message = messages[-1]
            # Access content attribute directly (AIMessage is not a dict)
            response_content = last_message.content if hasattr(last_message, 'content') else ""

            # Handle case where content might be a list of content blocks
            if isinstance(response_content, list):
                # Extract text from content blocks
                response_content = " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in response_content
                )

            # Extract metadata
            metadata = {
                "message_count": len(messages),
                "model_used": self.model,
                "thread_id": config["configurable"]["thread_id"],
            }

            logger.info(
                f"Agent response for {user_phone}: {response_content[:100]}... "
                f"({len(messages)} messages in conversation)"
            )

            return {
                "success": True,
                "response": response_content,
                "all_messages": messages,  # Include all messages for display
                "metadata": metadata,
                "error": None,
            }

        except Exception as e:
            logger.error(
                f"Error processing message for {user_phone}: {e}", exc_info=True
            )
            return {
                "success": False,
                "response": "",
                "metadata": {},
                "error": str(e),
            }

    def get_conversation_state(self, user_phone: str) -> Optional[Dict[str, Any]]:
        """
        Get the current conversation state for a user.

        Args:
            user_phone: User's phone number

        Returns:
            Conversation state dictionary or None
        """
        try:
            thread_id = f"guest-{user_phone}"

            # Get state from LangGraph checkpointer
            # Note: This is a simplified version - actual implementation
            # depends on how we want to expose agent state
            return {
                "thread_id": thread_id,
                "user_phone": user_phone,
                # Additional state can be retrieved from agent's checkpointer
            }

        except Exception as e:
            logger.error(f"Error getting conversation state: {e}", exc_info=True)
            return None


# Global singleton instance (initialized when needed)
_agent_instance: Optional[DeepAgentConcierge] = None


def get_agent() -> DeepAgentConcierge:
    """
    Get or create the global deep-agent concierge instance.

    Returns:
        DeepAgentConcierge instance
    """
    global _agent_instance

    if _agent_instance is None:
        logger.info("Creating new DeepAgentConcierge instance")
        _agent_instance = DeepAgentConcierge()

    return _agent_instance


def process_message(user_phone: str, message_content: str) -> Dict[str, Any]:
    """
    Convenience function to process a message through the deep-agent.

    Args:
        user_phone: User's phone number
        message_content: Message content

    Returns:
        Result dictionary from DeepAgentConcierge.process_message()
    """
    agent = get_agent()
    return agent.process_message(user_phone, message_content)
