"""Intent classification service for understanding user queries."""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies user messages into predefined intents.

    Intents:
    - quick_answer: Simple factual questions
    - project_deepdive: Project details request
    - experience_deepdive: Role/company details
    - code_walkthrough: Show code request
    - skill_assessment: Fit check for roles
    - comparison: Compare X vs Y
    - tour: Guided walkthrough
    - general: Default/unclear intent
    """

    # Intent patterns with keywords and phrases
    INTENT_PATTERNS = {
        "quick_answer": [
            r"\b(what|who|how many|is he|does he|can he)\b",
            r"\b(tech stack|stack|skills|experience years|years)\b",
            r"\b(email|contact|phone|linkedin|github)\b",
            r"\b(location|where|based)\b",
            r"\b(current role|current job|working at)\b",
        ],
        "project_deepdive": [
            r"\b(tell me (more )?about|explain|describe|details on)\b.*(project|sandbox|genai|rag|communication|dispatch)",
            r"\b(project|genai-sandbox|rag pipeline)\b.*(detail|more|explain|architecture)",
            r"\b(how did you (build|create|implement))\b",
            r"\b(architecture|design|structure)\b.*(project)",
        ],
        "experience_deepdive": [
            r"\b(tell me (more )?about|explain|describe|details on)\b.*(kogta|capri|voereir|tradeindia|experience|role|job)",
            r"\b(what did you do|responsibilities|achievements)\b.*(at|in|during)",
            r"\b(experience at|role at|work at)\b",
            r"\b(kogta|capri|voereir|tradeindia)\b",
        ],
        "code_walkthrough": [
            r"\b(show|display|see)\b.*(code|implementation|snippet)",
            r"\b(how (is|did you) implement)\b",
            r"\b(rate limit|chunking|async|rag pipeline)\b.*(code|implement)",
            r"\b(code for|implementation of)\b",
        ],
        "skill_assessment": [
            r"\b(fit|suitable|good|qualified)\b.*(for|as|role)",
            r"\b(genai|backend|python|senior)\b.*(role|engineer|developer|position)",
            r"\b(rate|assess|evaluate)\b.*(skills|experience|fit)",
            r"\b(match|suitable for|right for)\b.*(job|role|position)",
            r"\b(hire|hiring|recruitment)\b",
        ],
        "comparison": [
            r"\b(compare|comparison|difference|vs|versus)\b",
            r"\b(how does .* differ|what.s the difference)\b",
            r"\b(pro.? and con|trade.?off)\b",
        ],
        "tour": [
            r"\b(tour|walk me through|overview|introduction|start)\b",
            r"\b(guide|guided|walkthrough)\b",
            r"\b(show me around|explore)\b",
        ],
    }

    # Context-based intent boosters
    CONTEXT_BOOSTERS = {
        "projects": ["project_deepdive", "code_walkthrough"],
        "experience": ["experience_deepdive"],
        "skills": ["skill_assessment", "quick_answer"],
        "about": ["quick_answer"],
        "contact": ["quick_answer"],
    }

    def __init__(self):
        """Initialize the intent classifier."""
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_patterns = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            self.compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def classify(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Classify the intent of a user message.

        Args:
            message: The user's message
            context: Optional context including current_section, previous_topic, history

        Returns:
            The classified intent string
        """
        message = message.lower().strip()
        context = context or {}

        # Score each intent
        scores = {intent: 0.0 for intent in self.INTENT_PATTERNS.keys()}
        scores["general"] = 0.1  # Base score for general

        # Pattern matching
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(message):
                    scores[intent] += 1.0
                    break  # Only count once per intent

        # Context boosting
        current_section = context.get("current_section")
        if current_section and current_section in self.CONTEXT_BOOSTERS:
            for intent in self.CONTEXT_BOOSTERS[current_section]:
                if intent in scores:
                    scores[intent] += 0.3

        # Previous topic continuity
        previous_topic = context.get("previous_topic")
        if previous_topic:
            if previous_topic in ["project_deepdive", "code_walkthrough"]:
                scores["code_walkthrough"] += 0.2
                scores["project_deepdive"] += 0.2
            elif previous_topic == "experience_deepdive":
                scores["experience_deepdive"] += 0.2

        # Check for follow-up patterns
        follow_up_patterns = [
            r"^(tell me more|more details|explain|go on|continue)",
            r"^(what about|how about|and)",
            r"^(yes|sure|okay|please)",
        ]
        for pattern in follow_up_patterns:
            if re.match(pattern, message, re.IGNORECASE):
                # Boost previous topic's intent
                if previous_topic and previous_topic in scores:
                    scores[previous_topic] += 0.5
                break

        # Get the highest scoring intent
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]

        logger.debug(f"Intent scores: {scores}")
        logger.debug(f"Best intent: {best_intent} (score: {best_score})")

        # If no strong match, default to general
        if best_score < 0.5:
            return "general"

        return best_intent

    def get_all_intents(self) -> List[str]:
        """Return list of all possible intents."""
        return list(self.INTENT_PATTERNS.keys()) + ["general"]
