"""The plugin's own system-prompt section: end a choice with chips, not prose.

Hermes freezes it into each new session's prompt under "## Plugin Context: <name>".
The section is told the session's platform: Hermes Desktop gets the directive
rule, every other surface (Telegram, the CLI, …) is told to offer a numbered list
instead, because a raw ::followups line would arrive as text there.
"""

from __future__ import annotations

# Surfaces where the desktop half draws the directive.
DRAWS = frozenset({"local", "desktop"})

MAX_CHARS = 1_200

DESKTOP = (
    "This chat draws follow-up chips under a reply. When the next step is a choice, "
    "do not ask for it in prose: never end with \"say the word and I'll…\", "
    "\"want me to…?\", \"shall I…?\", a \"let me know\" line, or a list of things you "
    "could do next. End with this directive as the last paragraph of the reply, alone "
    "on its own line:\n"
    "::followups{multi=\"1\" q1=\"Push the branch and open the PR\" q2=\"Add a CHANGELOG entry\"}\n"
    "One qN per option, 2 to 5 of them, imperative and specific, under 120 characters "
    "each, most likely first. Keep multi=\"1\" when more than one can be done together; "
    "drop it when the options are exclusive. Never put the directive inside a sentence, "
    "a list or a code block, and never write it twice. Put what you did in the prose; the "
    "chips carry what can follow."
)

OTHER = (
    "This surface cannot draw follow-up chips, so never write a ::followups directive "
    "here. When offering next steps, end with a short numbered list of concrete options "
    "instead of an open question."
)


def chips_rule(session: dict) -> str:
    """The section's text for one session: the chip rule on the app, text-only elsewhere.

    {"platform": "local"} → DESKTOP;  {"platform": "telegram"} → OTHER;  {} → OTHER
    """
    return DESKTOP if (session or {}).get("platform") in DRAWS else OTHER
