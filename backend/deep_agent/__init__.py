"""
Deep-Agent powered hospitality concierge.

This module implements a LangChain deep-agent based AI assistant for the
hospitality platform, running in parallel with the existing message processor
for proof-of-concept evaluation.

Key components:
- tools.py: LangChain tools wrapping Django services
- prompts.py: System prompts for agents
- subagents.py: Specialized subagent configurations
- agent.py: Main deep-agent setup
- views.py: Parallel webhook endpoint
- tasks.py: Celery async processing
"""

__version__ = "0.1.0"
