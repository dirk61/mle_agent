"""LangGraph State schema for the MLE Agent.

Defines the TypedDict passed between all graph nodes.
See spec_state.md §3 for the authoritative field definitions.
"""

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Active ReAct loop history — wiped on macro-node transitions by Router.
    messages: Annotated[list, add_messages]

    # Persistent accumulator of all messages across all node transitions.
    # Never wiped. Router appends `messages` here before wiping `messages`.
    all_messages: Annotated[list, add_messages]

    # Brief instruction passed from the exiting node to the next.
    handoff_message: str

    # The active phase label (e.g. "data_engineering", "modeling").
    current_phase: str

    # Model tier for the next Action Node (e.g. "haiku", "sonnet", "opus").
    # Dictated by Router_Brain.
    target_model: str

    # Total Router transitions. Incremented by Router on each invocation.
    # Safety circuit breaker — Router routes to END when this exceeds max.
    iteration_count: int
