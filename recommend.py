"""Which of the offered next steps are worth doing now, from the decision classifier.

This module is the optional part of the plugin. The classifier is the `nerve`
plugin's `nerve_assess` tool (the older native `jev_assess` contract is accepted
too); without that plugin nothing here runs, no `rec` attribute is written, and the
chips render unmarked while everything else keeps working. Nothing in this module
is imported by the renderer, and nothing about the directive depends on it.

One `nerve_assess` call carries a question per option (up to 16 typed questions on
one shared state), so five options still cost one provider call of about 200 ms.
Every option the classifier puts at or above `MIN_TAKE_NOW` is recommended. That is
how more than one can be recommended at once: a categorical distribution can
clearly favour several candidates when they belong together, and the live shape is
0.81 / 0.79 / 0.77 for three steps that all have to happen.

No model is involved in the decision: labels in, indexes out. Nothing is
recommended when no classifier answers, and the directive stays valid without a
`rec` attribute.
"""

from __future__ import annotations

import json

# The classifier tools, in the order they are tried. `nerve_assess` is the name the
# nerve plugin registers; `jev_assess` is the older native name of the same contract.
RANKERS = ("nerve_assess", "jev_assess")

TAKE_NOW = "take it now"
LATER = "later"
SKIP = "skip"

# More likely than not: a candidate the distribution prefers over later-or-skip.
MIN_TAKE_NOW = 0.5
# Three marked chips is a recommendation; five marked chips is a wall of orange.
MAX_RECOMMENDED = 3
MAX_OPTIONS = 6

DEFAULT_STATE = "The assistant just finished a reply and is offering the user a few next steps."

ANSWER_INSTRUCTIONS = (
    "Should the assistant take this candidate next step right now, given the user's request "
    "and the work the reply just described? Judge it on its own: more than one candidate can "
    "deserve to be taken now."
)

CRITERIA = {
    TAKE_NOW: "The user would want this next step taken immediately.",
    LATER: "Reasonable, but not the thing to do next.",
    SKIP: "Not wanted.",
}


def questions(options: list[str]) -> dict[str, dict]:
    """One typed question per option, keyed by its chip number.

    ["Push it", "Tag it"] → {"q1": {"type": "choice", "instructions": "Option: Push it. Should …",
    "criteria": {"take it now": …, "later": …, "skip": …}}, "q2": {…}}
    """
    out: dict[str, dict] = {}
    for index, option in enumerate(options):
        out["q%d" % (index + 1)] = {
            "type": "choice",
            "instructions": "Option: %s. %s" % (option, ANSWER_INSTRUCTIONS),
            "criteria": dict(CRITERIA),
        }
    return out


def _probabilities(answer: object, label: str) -> float | None:
    if not isinstance(answer, dict):
        return None
    probabilities = answer.get("probabilities")
    if not isinstance(probabilities, dict):
        return None
    value = probabilities.get(label)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def scored(answers: dict, count: int) -> list[tuple[float, int]]:
    """(probability, index) for every option the classifier had an opinion on, best first."""
    out: list[tuple[float, int]] = []
    for index in range(count):
        probability = _probabilities(answers.get("q%d" % (index + 1)), TAKE_NOW)
        if probability is not None:
            out.append((probability, index))
    out.sort(key=lambda pair: (-pair[0], pair[1]))
    return out


def picks(answers: dict, count: int) -> list[int]:
    """The indexes to recommend, ascending, at most MAX_RECOMMENDED.

    Three options at 0.81 / 0.79 / 0.77 → [0, 1, 2];  an 0.91 favourite over 0.04s → [0];
    nothing at or above 0.5 → [].
    """
    if not isinstance(answers, dict) or count <= 0:
        return []
    keep = [index for probability, index in scored(answers, count) if probability >= MIN_TAKE_NOW]
    return sorted(keep[:MAX_RECOMMENDED])


def reply(options: list[str], answers: dict) -> str:
    """What the model reads: the attribute to write, or why there is none."""
    count = len(options)
    recommended = picks(answers, count)
    if not recommended:
        return (
            'No option reached %.2f on take-it-now, so leave rec out of the directive.' % MIN_TAKE_NOW
        )
    by_index = {index: probability for probability, index in scored(answers, count)}
    numbers = ",".join(str(index + 1) for index in recommended)
    detail = ", ".join("%d (%.2f)" % (index + 1, by_index[index]) for index in recommended)
    return 'Recommended %d of %d: %s. Write rec="%s" into the directive.' % (
        len(recommended),
        count,
        detail,
        numbers,
    )


def _answers_from(result: object) -> dict | None:
    """The answers map out of a dispatch result, which arrives as a JSON string."""
    payload = result
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            return None
    if not isinstance(payload, dict):
        return None
    if payload.get("ok") is False:
        return None
    answers = payload.get("answers")
    return answers if isinstance(answers, dict) and answers else None


def recommend(dispatch, options: list[str], context: str = "") -> str:
    """Ask the classifier, through `dispatch(tool_name, args)`, and phrase the answer.

    `dispatch` is ctx.dispatch_tool: it returns the handler's JSON string and may raise.
    """
    clean = [str(option).strip() for option in options if str(option).strip()]
    if len(clean) < 2:
        return "A recommendation needs at least two options; leave rec out."
    clean = clean[:MAX_OPTIONS]
    args = {
        "state": (str(context or "").strip() or DEFAULT_STATE),
        "questions": questions(clean),
    }
    for name in RANKERS:
        try:
            answers = _answers_from(dispatch(name, args))
        except Exception:  # a missing or broken classifier is not a reply failure
            continue
        if answers:
            return reply(clean, answers)
    return (
        "No decision classifier answered (%s), so leave rec out and offer the chips as they are."
        % ", ".join(RANKERS)
    )


FOLLOWUP_RECOMMEND_SCHEMA = {
    "name": "followup_recommend",
    "description": (
        "Ask the decision classifier which of the next steps you are about to offer are worth "
        "taking now, for the rec attribute of a ::followups directive. Returns the 1-based option "
        "numbers at or above the threshold, which can be more than one when several steps belong "
        "together. Call it before writing the directive when the chips are a real choice, then write "
        'rec="<numbers>" into it exactly as returned. If it reports no classifier, write the '
        "directive without rec."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": MAX_OPTIONS,
                "description": "The chips' option texts, in the order they will appear.",
            },
            "context": {
                "type": "string",
                "description": (
                    "One sentence on what the user asked for and what the reply just did. The "
                    "classifier judges every option against this, so name the goal."
                ),
            },
        },
        "required": ["options"],
    },
}


def handler(dispatch):
    """The tool handler: params in, the classifier's verdict out."""

    def followup_recommend(params: dict, **kwargs) -> str:
        del kwargs
        options = params.get("options") if isinstance(params, dict) else None
        if isinstance(options, str):
            options = options.split("\n")
        if not isinstance(options, list):
            return "followup_recommend needs an options array of at least two strings."
        return recommend(dispatch, options, str((params or {}).get("context") or ""))

    return followup_recommend
