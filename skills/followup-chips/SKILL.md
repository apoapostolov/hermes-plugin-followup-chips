---
name: followup-chips
description: Next-step chips for Hermes desktop replies.
version: 1.2.0
---

# followup-chips

End replies where a concrete next step exists with a `::followups` directive on its own final line. The desktop plugin (desktop-plugins/followup-chips/plugin.js) renders each `qN` as a clickable chip that sends the question as the next user turn.

## Rules

- Syntax, alone on the last line: `::followups{q1="..." q2="..." q3="..."}` — 2–3 questions; the renderer accepts q1..qN with no hard limit, but keep it ≤5.
- ALL attributes — including `title`, `other`, `otherLabel` — inside the same brace pair. Anything after the closing `}` becomes prose (visible as a literal `other=...` text). Full form: `::followups{title="..." q1="..." q2="..." other="true" otherLabel="..."}`.
- One `::followups` directive per reply. Two stacked blocks is an emit bug, not a plugin feature.
- Optional attrs, both opt-in: `title="Next steps"` draws a small label above the chips, `other="true"` appends one free-text row ("Other…", Enter sends it) for a remark the chips don't cover. Use them only when they add something.
- Context-specific next steps from this conversation, never generic ("Anything else?"). Long questions wrap.
- Skip for one-line answers, pure Q&A, and mid-task progress notes. Nothing after the directive.

## Reply types: kind="multi" and kind="answer" (v1.2.0)

Besides the default one-click chips, the plugin supports two interaction modes selected via the `kind` attribute. Choose based on WHAT the user must do with the items — never on language or topic; the attribute keys are language-neutral ASCII and `q`/`title` values are written in the language of the reply.

| End of the reply | directive | what the user sees |
|---|---|---|
| follow-up question, a single answer suffices | `::followups{q1="…"}` (as always) | one click sends |
| items the user answers per item ("Concretely:", "Next steps" with choices) | `… kind="answer" title="Concretely" q1="…" q2="…"` | checkbox + reply field per item; Send posts `1. <item>: <answer>` lines |
| items the user only selects from ("do 1 and 3") | `… kind="multi" q1="…" q2="…"` | checkboxes + one Send button |

Rules:

- Semantic trigger, never a literal word: "the reply ends with items the user can respond to per item" → `answer`. The lead-in phrase ("Concretely:", "Specifically") goes in `title=`, not as prose above it — otherwise it appears twice.
- Without `kind` (or an unknown value): exactly the old one-click behaviour. Fail-safe, never a blocker.
- In `answer`/`multi` blocks, items without typed text are sent as the bare numbered item — quick selection is never blocked.
- Keep items short: the directive body has a hard 2048-char limit (`DIRECTIVE_BODY_MAX`); longer lists are silently truncated.
- One interaction mode per block; do not combine `other="true"` with `kind` unless it truly adds value.

## "Next steps" lists are NEVER prose

A reply that ends with a next-steps list (a `**Next steps**` heading + bullets) renders as dead text — the plugin only draws directives. Emit instead:

`::followups{title="Next steps" q1="…" q2="…" q3="…"}`

The `title` attr IS the heading, and each item becomes a clickable option. Same for a reply that ends in follow-up questions: directive, not prose.

## Division of labour with the native clarify tool

Hermes already renders genuine multiple-choice questions with clickable options (the `clarify` tool: choices + an "Other" free-text row). Keep those there — do NOT rebuild them in the plugin. The plugin covers exactly one thing: the reply's own next-step fork. That keeps it single-directive and unbloated.

## Layout (fixed in plugin.js, do not re-tweak)

Chips stack vertically, left-aligned, `fit-content` width, wrap on long text, borderRadius 12, no ellipsis truncation.

## Hover idiom (fixed in plugin.js)

Hover runs the Hermes `arc-border` travelling-light ring — TWO layers, exactly like the app's styles.css: `.fu-arc` masked-ring wrapper (inset -0.125rem, padding 0.078125rem, mask-composite xor) + `.fu-arc::before` 240% gradient translated by keyframes. NEVER merge both onto one pseudo: `inset` + `width:240%` on one element makes the ring pump large→small. Colors via `--arc-c1/c2` keyed to `--dt-primary`. Theme vars only.

## jsx runtime pitfall

See the `hermes-agent` skill's desktop-plugins reference: `jsx()`'s 3rd arg is the key, children go in `props.children`, never pass null props. The arc is pure CSS `.fu-chip::after` — no extra element.

## Choice state machine (fixed in plugin.js)

Click = chosen (✓, primary tint; others dim 72%) + running: arc spins until the session's `message.complete` gateway event (via ctx.onEvent) settles it to resting-chosen. `message.start` also settles stuck states. Never pass null as jsx props; children go in props.

## Per-block state keys

State key = `<sessionId>::<source>` — the render args' `source` (raw directive text) is the unique block id, exactly like the app keys directive instances. WITHOUT it, `chosen` leaks from one followups block into the next (looks pre-selected). Settle handlers prefix-match `sid::` across all groups.

## Single active arc

Only the MOST RECENT choice runs its arc (module `activeKey`; `setActive()` stops running on all other groups + re-emits so they re-render resting). Older blocks keep ✓ chosen style but never arc. Settle clears activeKey.

## Persistence

Choices survive reload via `ctx.storage` (sync, namespaced `hermes.plugin.<id>.*`): bind it in register, `storage.get('choices', {})` on hydrate, `persistChoice()` on every click. `running` is transient - never persisted. Verified: storage lands in Local Storage leveldb as `hermes.plugin.followup-chips.choices`.

## Trigger shape (test questions)

Chips appear when the answer solves something and a natural next fork exists. Strong triggers: "help me set up X", "can you build X", "walk me through X", multi-step how-to. Weak (correctly NO chips): one-word answers, pure factual Q&A, opinion questions, "what is X". Model test-recipe: fresh session + strong-trigger question; no directive after a strong answer = that model's emit discipline is the problem, not the plugin.

## Model-agnosticism — VERIFIED grok 4.7 (nov 12)

Zero model/provider coupling in the plugin: the ONLY model-dependent part is the directive emit (Rules section) = prompt discipline. Verified live: grok-4.7 emits ::followups on follow-up turns; first answer in a fresh session may skip it (no fork context yet) - correct per rules, not a bug. Renderer/composer/gateway events are app-layer, model-blind.

## Deployment (both halves, every profile)

Two independent halves: the plugin renders chips (user-side UI only — the agent never sees the click, it just arrives as the next user turn); the agent emits `::followups` only because THIS skill tells it to. Installing one without the other yields nothing. Each Hermes profile is its own install root, so cover `desktop-plugins/followup-chips/plugin.js` AND the skill copy in the root profile and in every `profiles/<name>/` on the host, then verify per copy by md5 (see the `hermes-agent` skill's desktop-plugins reference, "Profile fan-out"). `ctx.storage` choices are per-profile — expected, not a bug.

## Contest film pipeline

See the `demo-video` skill for the reusable record → edge-tts VO → ffmpeg-montage pipeline and its pitfalls (window-rect gdigrab take, background recording job, ffprobe verify, scratch-prune warning). This plugin's contest film: 54s, window-only capture, en-US-AndrewNeural VO, 1920x1080 pillarbox. User X-handle: nuonrg.

## Catalog CI quirks (learned during submission)

New contributors: the `Repository guards` check wants a `contributors/emails/<email>` mapping file (one line: login) - add it ON the PR branch as an extra commit. The first push after a head-change may need a rebase; the bot may merge main into your branch (harmless). Fork PR checks sit at `action_required` until a maintainer approves workflows - just wait, optionally leave a polite PR comment pointing at the fix.

## git state pitfalls (the Windows host)

No global git config: pass `-c user.name/-c user.email` on every commit/rebase. A worktree rebase blocks `branch -f` - use `reset --hard <sha>`. The fork copy inside the scratch cache dies on scratch-prune; the plugin repo under %LOCALAPPDATA% persists.

## Parser lesson: attr names are lowercased

The desktop parser (`parseAttrs` in transcript-directives.ts) does `attrs[key.toLowerCase()]` — `otherLabel="x"` arrives as `otherlabel`. Attribute lookups in plugin.js must accept both spellings (`attrs.otherLabel || attrs.otherlabel`) or use the lowercase key directly. camelCase attrs fail silently as undefined, no error.

## Tag hygiene: never move a published tag

A tag with a GitHub Release attached is immutable. A post-release fix = patch bump (1.1.0 stays; the fix becomes 1.1.1). The v1.1.0 tag was force-moved twice during that release — do not repeat that; release.sh runs tag/validate/release only after render verification.

## Release flow v2 (nov 2026)

Build host: the epyc box, project dir `~/projects/followup-chips/` — containing `hermes-plugin-followup-chips/` (this repo), `hermes-agent-catalog/` (shallow clone of upstream for the pin) and `release.sh` (bump → validate → push → catalog-branch → PR; gh lives in `~/.local/bin`, token via `gh auth login --with-token`). Windows stays the render/test host: after every release copy plugin.js to `%LOCALAPPDATA%/hermes/desktop-plugins/followup-chips/` + reload desktop plugins. v1.1.0: repo `6aff2a1`, pin-PR #157831 (clean single commit, MERGEABLE), tag `v1.1.0`. The fork's main lags upstream — release.sh therefore branches from upstream's `origin/main`, not the fork.

## Contest submission (Nov 2026) — MERGED 🎉

PR #154186 merged 12 Nov 10:59 UTC by Nous into main. The plugin is officially catalog-listed: plugin-catalog/followup-chips.yaml on main (pin 3e44fa9, maintainer nuonrg). Installable via `hermes plugins install followup-chips`; the docs page /docs/plugins/followup-chips is generated automatically. Repo: github.com/nuonrg/hermes-plugin-followup-chips. Contest result: pending.

## Catalog repo layout (submission doc)

A pinned tree MUST have a `plugin.yaml` manifest (name/label/version/author/homepage/description/tags — cf hermes-official-plugins/accent-picker) + entrypoint at `desktop/plugin.js`. Validate first: `hermes plugins validate <dir> --install-deps`. The PR adds ONE file `plugin-catalog/<name>.yaml` to NousResearch/hermes-agent; fork+branch, never push directly.
