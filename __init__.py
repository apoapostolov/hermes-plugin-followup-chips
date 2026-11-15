"""followup-chips: clickable follow-up chips, and the rule that fills them.

The desktop half (desktop/plugin.js) draws a `::followups{…}` paragraph as chips
under a reply. This half gives the model the rule that ends a choice with that
directive, and, when the owner turns on `auto_offers`, converts a closing offer
the model wrote in prose anyway into the same directive before the reply is
stored and drawn.

Both halves are optional: the plugin works as a single file dropped into
desktop-plugins/, where the model emits the directive on its own.
"""

from __future__ import annotations

from .offers import rewrite
from .prompt_section import MAX_CHARS, chips_rule

NAME = "followup-chips"
SETTING = "auto_offers"


def offer_hook(response_text: str = "", platform: str = "", auto_offers: bool = False) -> str | None:
    """The reply with its closing offer drawn as chips, or None to leave it alone.

    Off by default: a hook that rewrites replies is opt-in, and the prompt section
    already asks for the directive.
    """
    if not auto_offers or not isinstance(response_text, str):
        return None
    return rewrite(response_text, platform=platform)


def register(ctx) -> None:
    ctx.register_system_prompt_section(NAME, chips_rule, max_chars=MAX_CHARS)

    def transform(response_text: str = "", platform: str = "", **kwargs) -> str | None:
        del kwargs
        try:
            enabled = bool(ctx.get_config(SETTING, False))
        except Exception:  # an unreadable setting must not break a reply
            enabled = False
        return offer_hook(response_text=response_text, platform=platform, auto_offers=enabled)

    ctx.register_hook("transform_llm_output", transform)
