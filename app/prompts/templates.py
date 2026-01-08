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
# Actions:
#   code: fetches from CodeHandler (rate_limiting, rag_pipeline, chunking, async_calls)
#   deepdive: sends chat message "Tell me more about {target}"
#   compare: fetches from CodeHandler (rag_vs_backend, chunking_strategies)
SUGGESTION_TEMPLATES = {
    "quick_answer": [
        {"label": "Tell me about projects", "action": "deepdive", "target": "projects"},
        {"label": "What's the work experience?", "action": "deepdive", "target": "work experience"},
    ],
    "project_deepdive": [
        {"label": "Show me the code", "action": "code", "target": "rag_pipeline"},
        {"label": "Architecture details", "action": "deepdive", "target": "the architecture"},
        {"label": "What challenges were faced?", "action": "deepdive", "target": "challenges faced"},
        {"label": "Compare with other projects", "action": "compare", "target": "rag_vs_backend"},
    ],
    "experience_deepdive": [
        {"label": "Key achievements", "action": "deepdive", "target": "key achievements"},
        {"label": "Tech stack used", "action": "deepdive", "target": "technologies used"},
        {"label": "Team collaboration", "action": "deepdive", "target": "team collaboration"},
    ],
    "code_walkthrough": [
        {"label": "Show rate limiting code", "action": "code", "target": "rate_limiting"},
        {"label": "Show RAG pipeline code", "action": "code", "target": "rag_pipeline"},
        {"label": "Show chunking code", "action": "code", "target": "chunking"},
        {"label": "Show async code", "action": "code", "target": "async_calls"},
    ],
    "skill_assessment": [
        {"label": "GenAI experience details", "action": "deepdive", "target": "GenAI experience"},
        {"label": "Backend skills details", "action": "deepdive", "target": "backend skills"},
        {"label": "Projects demonstrating skills", "action": "deepdive", "target": "projects"},
    ],
    "comparison": [
        {"label": "RAG vs Backend comparison", "action": "compare", "target": "rag_vs_backend"},
        {"label": "Chunking strategies", "action": "compare", "target": "chunking_strategies"},
    ],
    "tour": [
        {"label": "Technical skills", "action": "deepdive", "target": "technical skills"},
        {"label": "Projects", "action": "deepdive", "target": "projects"},
        {"label": "Work experience", "action": "deepdive", "target": "work experience"},
        {"label": "Contact information", "action": "deepdive", "target": "contact info"},
    ],
    "general": [
        {"label": "About Deepanshu", "action": "deepdive", "target": "Deepanshu Malik"},
        {"label": "Skills overview", "action": "deepdive", "target": "skills"},
        {"label": "Projects overview", "action": "deepdive", "target": "projects"},
        {"label": "Work experience", "action": "deepdive", "target": "work experience"},
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
