"""Scope guardrails: this agent does exactly one job — AMS flex-date flight
search chat — and nothing else. Enforced in code (not just prompt wording),
so a jailbreak attempt or a hallucinated tool call can't widen the surface.
"""
from __future__ import annotations

import re

MAX_MESSAGE_LEN = 800

# Only this tool may ever be invoked. Anything else the model asks for is
# refused before it runs, regardless of how the model was persuaded to ask.
ALLOWED_TOOLS = {"search_flights"}

# Off-topic asks we refuse outright, without spending a model call on them:
# general coding help, web search / browsing, content generation unrelated to
# flights, and prompt-injection attempts trying to change the agent's role.
_BLOCKED_PATTERNS = [
    r"\bwrite\s+(a|some|the)?\s*(code|script|function|program|sql|regex)\b",
    r"\b(python|javascript|typescript|java|c\+\+|bash|shell)\s+(code|script|snippet)\b",
    r"\bdebug\s+(my|this|the)\s+code\b",
    r"\bsearch\s+the\s+(web|internet)\s+for\b",
    r"\bgoogle\s+(this|that|for)\b",
    r"\blatest\s+news\b",
    r"\bwrite\s+(an?\s+)?(essay|poem|story|song|blog post)\b",
    r"\bsolve\s+(this|the)\s+(equation|math|homework)\b",
    r"\bgenerate\s+(an?\s+)?(image|picture|photo)\b",
    r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b",
    r"\byou\s+are\s+now\b",
    r"\bact\s+as\s+(a|an)\b(?!.*flight)",
    r"\breveal\s+(your|the)\s+(system\s+prompt|instructions)\b",
    r"\bwhat\s+is\s+your\s+system\s+prompt\b",
]
_BLOCKED_RE = re.compile("|".join(_BLOCKED_PATTERNS), re.IGNORECASE)

REFUSAL_MESSAGE = (
    "I can only help with flexible-date flight search out of Amsterdam Schiphol "
    "(AMS) — destinations, date ranges, and price comparisons. I can't help with "
    "coding, general web search, or anything outside flight search. Ask me about "
    "a route or travel dates instead!"
)

TOO_LONG_MESSAGE = (
    f"That message is a bit long for me — please keep flight questions under "
    f"{MAX_MESSAGE_LEN} characters."
)


def check_user_message(message: str) -> str | None:
    """Returns a refusal string if the message should be blocked, else None."""
    if len(message) > MAX_MESSAGE_LEN:
        return TOO_LONG_MESSAGE
    if _BLOCKED_RE.search(message):
        return REFUSAL_MESSAGE
    return None


def is_tool_allowed(tool_name: str) -> bool:
    return tool_name in ALLOWED_TOOLS


_CODE_FENCE_RE = re.compile(r"```")


def sanitize_reply(reply: str | None) -> str:
    """Belt-and-braces output check: strip code fences if the model slips one in."""
    if not reply:
        return reply
    if _CODE_FENCE_RE.search(reply):
        reply = _CODE_FENCE_RE.sub("", reply)
    return reply
