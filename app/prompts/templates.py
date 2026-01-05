"""Response templates and formatting utilities."""

from typing import Any, Dict, List


def format_context(retrieved_docs: List[Dict[str, Any]]) -> str:
    """
    Format retrieved documents into a context string.

    Args:
        retrieved_docs: List of documents with content and metadata

    Returns:
        Formatted context string
    """
    if not retrieved_docs:
        return ""

    context_parts = []
    for doc in retrieved_docs:
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})
        category = metadata.get("category", "")
        source = metadata.get("source", "")

        # Add source info if available
        header = ""
        if category:
            header = f"[{category.upper()}]"
        if source:
            header += f" {source}"

        if header:
            context_parts.append(f"{header}\n{content}")
        else:
            context_parts.append(content)

    return "\n\n---\n\n".join(context_parts)


# Suggestion templates by intent
SUGGESTION_TEMPLATES = {
    "quick_answer": [
        {"label": "Tell me more", "action": "deepdive", "target": "more_details"},
        {"label": "See projects", "action": "deepdive", "target": "projects"},
    ],
    "project_deepdive": [
        {"label": "Show Code", "action": "code", "target": "rag_pipeline"},
        {"label": "Architecture", "action": "deepdive", "target": "rag_architecture"},
        {"label": "Challenges", "action": "deepdive", "target": "rag_challenges"},
        {"label": "Compare Projects", "action": "compare", "target": "rag_vs_backend"},
    ],
    "experience_deepdive": [
        {"label": "Key Achievements", "action": "deepdive", "target": "achievements"},
        {"label": "Tech Stack Used", "action": "deepdive", "target": "tech_stack"},
        {"label": "Team & Mentorship", "action": "deepdive", "target": "mentorship"},
    ],
    "code_walkthrough": [
        {"label": "Rate Limiting", "action": "code", "target": "rate_limiting"},
        {"label": "RAG Pipeline", "action": "code", "target": "rag_pipeline"},
        {"label": "Chunking", "action": "code", "target": "chunking"},
        {"label": "Async Calls", "action": "code", "target": "async_calls"},
    ],
    "skill_assessment": [
        {"label": "GenAI Fit", "action": "deepdive", "target": "genai_fit"},
        {"label": "Backend Fit", "action": "deepdive", "target": "backend_fit"},
        {"label": "See Projects", "action": "deepdive", "target": "projects"},
    ],
    "comparison": [
        {"label": "RAG vs Backend", "action": "compare", "target": "rag_vs_backend"},
        {"label": "Chunking Strategies", "action": "compare", "target": "chunking_strategies"},
    ],
    "tour": [
        {"label": "Skills", "action": "deepdive", "target": "skills"},
        {"label": "Projects", "action": "deepdive", "target": "projects"},
        {"label": "Experience", "action": "deepdive", "target": "experience"},
        {"label": "Contact", "action": "deepdive", "target": "contact"},
    ],
    "general": [
        {"label": "About Me", "action": "deepdive", "target": "about"},
        {"label": "See Skills", "action": "deepdive", "target": "skills"},
        {"label": "View Projects", "action": "deepdive", "target": "projects"},
        {"label": "Experience", "action": "deepdive", "target": "experience"},
    ],
}


def get_suggestion_templates(intent: str) -> List[Dict[str, str]]:
    """Get suggestion templates for a given intent."""
    return SUGGESTION_TEMPLATES.get(intent, SUGGESTION_TEMPLATES["general"])


# Response format templates
RESPONSE_FORMATS = {
    "checklist": """
{title}

{items}

{summary}
""",
    "comparison_table": """
| {headers} |
|{divider}|
{rows}
""",
    "project_overview": """
## {name}

{description}

**Tech Stack:** {tech_stack}

**Key Features:**
{features}

{links}
""",
}


def format_checklist(
    title: str,
    items: List[Dict[str, str]],
    summary: str = "",
) -> str:
    """Format a checklist response."""
    formatted_items = []
    for item in items:
        status = item.get("status", "neutral")
        icon = {"strong": "✅", "progress": "🔄", "gap": "⚠️"}.get(status, "•")
        text = item.get("text", "")
        formatted_items.append(f"{icon} {text}")

    return RESPONSE_FORMATS["checklist"].format(
        title=title,
        items="\n".join(formatted_items),
        summary=summary,
    )


def format_project(
    name: str,
    description: str,
    tech_stack: List[str],
    features: List[str],
    links: Dict[str, str] = None,
) -> str:
    """Format a project overview response."""
    return RESPONSE_FORMATS["project_overview"].format(
        name=name,
        description=description,
        tech_stack=", ".join(tech_stack),
        features="\n".join([f"- {f}" for f in features]),
        links=", ".join([f"[{k}]({v})" for k, v in (links or {}).items()]),
    )
