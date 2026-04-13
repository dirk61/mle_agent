"""LangGraph StateGraph construction for the MLE Agent.

Builds the graph:
    System_Architect -> Router_Brain <-> {Action Nodes | END}

All Action Nodes have internal ReAct loops (no graph-level tool edges).
Router_Brain dispatches based on current_phase set during its node execution.

See spec_state.md Node Definitions for authoritative edge rules.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.nodes import (
    make_action_node,
    router_brain_node,
    system_architect_node,
)
from src.state import AgentState


def _route_from_router(state: AgentState) -> str:
    """Determine next node based on Router's current_phase decision.

    Maps phase labels (set by router_brain_node) to graph node names.
    Returns END when the Router decides the pipeline is complete.
    """
    phase = state.get("current_phase", "END")
    return {
        "architecture": "System_Architect",
        "data_engineering": "Data_Engineer",
        "model_engineering": "Model_Engineer",
        "evaluation": "Evaluator",
        "END": END,
    }.get(phase, END)


def build_graph():
    """Build and compile the MLE Agent StateGraph.

    Returns a compiled graph ready for invoke() / ainvoke().
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ───────────────────────────────────────────────────
    graph.add_node("System_Architect", system_architect_node)
    graph.add_node("Router_Brain", router_brain_node)
    graph.add_node("Data_Engineer", make_action_node("Data_Engineer"))
    graph.add_node("Model_Engineer", make_action_node("Model_Engineer"))
    graph.add_node("Evaluator", make_action_node("Evaluator"))

    # ── Edges ────────────────────────────────────────────────────────────
    # All Action Nodes exit to Router_Brain
    graph.add_edge("System_Architect", "Router_Brain")
    graph.add_edge("Data_Engineer", "Router_Brain")
    graph.add_edge("Model_Engineer", "Router_Brain")
    graph.add_edge("Evaluator", "Router_Brain")

    # Router conditionally dispatches to next Action Node or END
    graph.add_conditional_edges(
        "Router_Brain",
        _route_from_router,
        {
            "System_Architect": "System_Architect",
            "Data_Engineer": "Data_Engineer",
            "Model_Engineer": "Model_Engineer",
            "Evaluator": "Evaluator",
            END: END,
        },
    )

    # ── Entry point ──────────────────────────────────────────────────────
    graph.set_entry_point("System_Architect")

    return graph.compile()
