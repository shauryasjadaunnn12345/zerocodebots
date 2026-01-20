from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TypedDict, Type


class WorkflowNode(TypedDict):
    """
    JSON schema for a workflow node.

    Example:
    {
      "id": "classify",
      "type": "classify_intent",
      "config": { ... }
    }
    """

    id: str
    type: str
    config: Dict[str, Any]


class WorkflowEdge(TypedDict):
    """
    JSON schema for a workflow edge.

    Example:
    {
      "from": "classify",
      "to": "respond",
      "condition": "answer"   # free-form label, used by routers
    }
    """

    from_: str  # "from" in JSON
    to: str
    condition: Any


class WorkflowDefinition(TypedDict, total=False):
    """
    Top-level workflow JSON schema.

    {
      "nodes": [ ... ],
      "edges": [ ... ]
    }
    """

    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


WORKFLOW_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "config"],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "type": {"type": "string", "minLength": 1},
                    "config": {"type": "object"},
                },
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["from", "to"],
                "properties": {
                    "from": {"type": "string", "minLength": 1},
                    "to": {"type": "string", "minLength": 1},
                    # `condition` is free-form; strings work well with routers
                    "condition": {},
                },
            },
        },
    },
    "required": ["nodes", "edges"],
}


def validate_workflow_json(data: Dict[str, Any]) -> List[str]:
    """
    Lightweight validator for workflow JSON.

    Returns a list of human-readable error strings. If the list is empty,
    the workflow is considered valid.
    """
    errors: List[str] = []

    if not isinstance(data, dict):
        return ["Workflow must be a JSON object."]

    nodes = data.get("nodes")
    edges = data.get("edges")

    if not isinstance(nodes, list) or not nodes:
        errors.append("'nodes' must be a non-empty array.")
    if not isinstance(edges, list):
        errors.append("'edges' must be an array.")

    if errors:
        return errors

    node_ids: Dict[str, str] = {}
    for idx, raw_node in enumerate(nodes):
        if not isinstance(raw_node, dict):
            errors.append(f"nodes[{idx}] must be an object.")
            continue

        node_id = raw_node.get("id")
        node_type = raw_node.get("type")
        config = raw_node.get("config")

        if not isinstance(node_id, str) or not node_id.strip():
            errors.append(f"nodes[{idx}].id must be a non-empty string.")
        elif node_id in node_ids:
            errors.append(f"Duplicate node id '{node_id}'.")
        else:
            node_ids[node_id] = node_type or ""

        if not isinstance(node_type, str) or not node_type.strip():
            errors.append(f"nodes[{idx}].type must be a non-empty string.")

        if not isinstance(config, dict):
            errors.append(f"nodes[{idx}].config must be an object.")

    for idx, raw_edge in enumerate(edges or []):
        if not isinstance(raw_edge, dict):
            errors.append(f"edges[{idx}] must be an object.")
            continue

        from_id = raw_edge.get("from")
        to_id = raw_edge.get("to")

        if not isinstance(from_id, str) or not from_id.strip():
            errors.append(f"edges[{idx}].from must be a non-empty string.")
        elif from_id not in node_ids:
            errors.append(f"edges[{idx}].from refers to unknown node '{from_id}'.")

        if not isinstance(to_id, str) or not to_id.strip():
            errors.append(f"edges[{idx}].to must be a non-empty string.")
        elif to_id not in node_ids:
            errors.append(f"edges[{idx}].to refers to unknown node '{to_id}'.")

    return errors


# LangGraph integration (optional).
try:  # pragma: no cover - optional dependency
    from langgraph.graph import StateGraph, START, END

    LANGGRAPH_AVAILABLE = True
except Exception:
    StateGraph = None  # type: ignore
    START = None  # type: ignore
    END = None  # type: ignore
    LANGGRAPH_AVAILABLE = False


def build_langgraph_from_workflow(
    workflow: Dict[str, Any],
    state_type: Type[Any],
    node_functions: Dict[str, Callable[[Any], Any]],
    routers: Optional[Dict[str, Callable[[Any], str]]] = None,
):
    """
    Convert a validated workflow JSON definition into a LangGraph app.

    - `workflow` must follow the JSON schema defined above.
    - `state_type` is the TypedDict / dataclass representing the graph state.
    - `node_functions` maps node IDs to Python callables used as graph nodes.
    - `routers` optionally maps node IDs to routing functions used to decide
      which `condition` label to follow from a branching node.

    This function does NOT persist anything or touch Django; it simply returns
    a compiled LangGraph app that can be invoked per chat request.
    """
    if not LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph is not installed; cannot build workflow graph.")

    errors = validate_workflow_json(workflow)
    if errors:
        raise ValueError(f"Invalid workflow definition: {errors}")

    routers = routers or {}
    nodes = workflow["nodes"]
    edges = workflow["edges"]

    graph = StateGraph(state_type)

    # Add all nodes with their corresponding functions.
    for node in nodes:
        node_id = node["id"]
        if node_id not in node_functions:
            raise KeyError(f"No node function provided for node id '{node_id}'.")
        graph.add_node(node_id, node_functions[node_id])

    # Group edges by source node to detect branching points.
    edges_by_from: Dict[str, List[Dict[str, Any]]] = {}
    for edge in edges:
        from_id = edge["from"]
        edges_by_from.setdefault(from_id, []).append(edge)

    for from_id, group in edges_by_from.items():
        if len(group) == 1 or from_id not in routers:
            # Single edge or no router provided: simple linear edge(s).
            for edge in group:
                graph.add_edge(edge["from"], edge["to"])
        else:
            # Conditional routing using a router function.
            router = routers[from_id]
            mapping: Dict[str, str] = {}
            for edge in group:
                label = edge.get("condition")
                if not isinstance(label, str) or not label:
                    raise ValueError(
                        f"Conditional edges from '{from_id}' must have a non-empty "
                        f"string 'condition'. Problematic edge: {edge}"
                    )
                mapping[label] = edge["to"]

            # Use the first target as a safe default branch.
            default_target = group[0]["to"]
            graph.add_conditional_edges(from_id, router, mapping, default_target)

    # Link START and END automatically:
    # - START → all nodes that have no incoming edges.
    # - All nodes with no outgoing edges → END.
    all_node_ids = {n["id"] for n in nodes}
    from_ids = {e["from"] for e in edges}
    to_ids = {e["to"] for e in edges}

    start_candidates = sorted(all_node_ids - to_ids)
    end_candidates = sorted(all_node_ids - from_ids)

    if start_candidates:
        # Use the first start candidate as graph START.
        graph.add_edge(START, start_candidates[0])

    for node_id in end_candidates:
        graph.add_edge(node_id, END)

    return graph.compile()



