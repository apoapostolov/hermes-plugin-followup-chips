"""followup-chips: clickable follow-up chips, the rule that fills them, and the picker.

The desktop half (desktop/plugin.js) draws a `::followups{…}` paragraph as chips
under a reply. This half gives the model the rule that ends a choice with that
directive, converts a closing offer it wrote in prose anyway (opt-in), and exposes
`followup_recommend`, which asks the decision classifier which of the options are
worth taking now so the chips arrive pre-picked.

Both halves are optional: the plugin works as a single file dropped into
desktop-plugins/, where the model emits the directive on its own.
"""

from __future__ import annotations

from .offers import rewrite
from .prompt_section import MAX_CHARS, chips_rule
from .recommend import FOLLOWUP_RECOMMEND_SCHEMA, handler as recommend_handler

NAME = "followup-chips"
TOOLSET = NAME.replace("-", "_")
SETTING = "auto_offers"
RECOMMEND_SETTING = "auto_recommend"
# Plugins that register the decision classifier (`nerve_assess`, or the older
# `jev_assess` name of the same contract).
RANKER_PLUGINS = ("nerve", "jev")


def offer_hook(response_text: str = "", platform: str = "", auto_offers: bool = False) -> str | None:
    """The reply with its closing offer drawn as chips, or None to leave it alone.

    Off by default: a hook that rewrites replies is opt-in, and the prompt section
    already asks for the directive.
    """
    if not auto_offers or not isinstance(response_text, str):
        return None
    return rewrite(response_text, platform=platform)


def has_ranker(ctx) -> bool:
    """Whether a decision classifier plugin is loaded. Advisory: the tool degrades on its own."""
    for plugin_id in RANKER_PLUGINS:
        try:
            if ctx.has_plugin(plugin_id):
                return True
        except Exception:
            continue
    return False


def _config(ctx, key: str, default):
    try:
        return ctx.get_config(key, default)
    except Exception:  # an unreadable setting store must not break registration
        return default


def section_text(session: dict, recommends: bool = False) -> str:
    """The prompt section for one session (the section is a callable, so this runs per session)."""
    return chips_rule(session, recommends=recommends)


def register(ctx) -> None:
    # Only tell the agent to ask a classifier when there is one, and when the owner
    # has left recommendations on. The tool itself is always registered: plugins load
    # in an order we do not control, so probing once by name is advisory only.
    recommends = bool(_config(ctx, RECOMMEND_SETTING, True)) and has_ranker(ctx)
    ctx.register_system_prompt_section(
        NAME,
        lambda session: section_text(session, recommends=recommends),
        max_chars=MAX_CHARS,
    )

    ctx.register_tool(
        name="followup_recommend",
        toolset=TOOLSET,
        schema=FOLLOWUP_RECOMMEND_SCHEMA,
        handler=recommend_handler(ctx.dispatch_tool),
        description="Rank the next steps you are about to offer, for the rec attribute of the chips.",
        emoji="🎯",
    )

    def transform(response_text: str = "", platform: str = "", **kwargs) -> str | None:
        del kwargs
        try:
            enabled = bool(ctx.get_config(SETTING, False))
        except Exception:  # an unreadable setting must not break a reply
            enabled = False
        return offer_hook(response_text=response_text, platform=platform, auto_offers=enabled)

    ctx.register_hook("transform_llm_output", transform)
