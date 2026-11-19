---
name: followup-chips
description: Next-step chips for Hermes desktop replies.
version: 1.0.0
---

# followup-chips

End replies where a concrete next step exists with a `::followups` directive on its own final line. The desktop plugin (desktop-plugins/followup-chips/plugin.js) renders each `qN` as a clickable chip that sends the question as the next user turn.

## Rules

- Syntax, alone on the last line: `::followups{q1="..." q2="..." q3="..."}` — 2–3 questions; the renderer accepts q1..qN with no hard limit, but keep it ≤5.
- ALLE attributen — ook `title`, `other`, `otherLabel` — binnen hetzelfde accolade-paar. Alles ná de sluitende `}` wordt proza (zichtbaar als letterlijke `other=...` tekst). Volledige vorm: `::followups{title="..." q1="..." q2="..." other="true" otherLabel="..."}`.
- Één `::followups`-directive per antwoord. Twee blokken onder elkaar is een emissiefout, geen plugin-feature.
- Optional attrs, both opt-in: `title="Vervolgstappen"` draws a small label above the chips, `other="true"` appends one free-text row ("Anders…", Enter sends it) for a remark the chips don't cover. Use them only when they add something.
- Context-specific next steps from this conversation, never generic ("Anything else?"). Long questions wrap.
- Skip for one-line answers, pure Q&A, and mid-task progress notes. Nothing after the directive.

## "Vervolgstappen" / next-steps lists are NEVER prose

A reply that ends with a next-steps list (the model's habit: a `**Vervolgstappen**` heading + bullets) renders as dead text — the plugin only draws directives. Emit instead:

`::followups{title="Vervolgstappen" q1="…" q2="…" q3="…"}`

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

Chips appear when the answer solves something and a natural next fork exists. Strong triggers: "help me X op te zetten/in te stellen", "kun je X maken", "loop X met me door", multi-step how-to. Weak (correctly NO chips): één-woord antwoorden, pure feitelijke Q&A, meningsvragen, "wat is X". Model test-recipe: nieuwe sessie + sterk-trigger vraag; geen directive na sterk antwoord = emit-discipline van dat model is het probleem, niet de plugin.

## Model-agnosticism — VERIFIED grok 4.7 (nov 12)

Zero model/provider coupling in the plugin: the ONLY model-dependent part is the directive emit (Rules section) = prompt discipline. Verified live: grok-4.7 emits ::followups on follow-up turns; first answer in a fresh session may skip it (no fork context yet) - correct per rules, not a bug. Renderer/composer/gateway events are app-layer, model-blind.

## Deployment (both halves, every profile)

Two independent halves: the plugin renders chips (user-side UI only — the agent never sees the click, it just arrives as the next user turn); the agent emits `::followups` only because THIS skill tells it to. Installing one without the other yields nothing. Each Hermes profile is its own install root, so cover `desktop-plugins/followup-chips/plugin.js` AND `skills/productivity/followup-chips/SKILL.md` in the root profile and in every `profiles/<name>/` on the host, then verify per copy by md5 (see the `hermes-agent` skill's desktop-plugins reference, "Profile fan-out"). `ctx.storage` choices are per-profile — expected, not a bug.

## Contest film pipeline

See the `demo-video` skill for the reusable record → edge-tts VO → ffmpeg-montage pipeline and its pitfalls (window-rect gdigrab take, background recording job, ffprobe verify, scratch-prune warning). This plugin's winning film: 54s, window-only capture, en-US-AndrewNeural VO, 1920x1080 pillarbox. User X-handle: nuonrg.

## Catalog CI quirks (learned during submission)

New contributors: `Repository guards` check wants `contributors/emails/<email>` mapping file (one line: login) - add ON the PR branch as extra commit. First push after head-change may need rebase; bot may merge main into your branch (harmless). Fork PR checks sit at `action_required` until a maintainer approves workflows - just wait, optionally leave a polite PR comment pointing at the fix.

## git state pitfalls (this machine)

No global git config: pass `-c user.name/-c user.email` on every commit/rebase. Worktree rebase blocks `branch -f` - use `reset --hard <sha>`. The fork at cache/scratch dies with scratch-prune; plugin repo at %LOCALAPPDATA% persists.

## Parser les: attr-namen worden gelowercased

De desktop parser (`parseAttrs` in transcript-directives.ts) doet `attrs[key.toLowerCase()]` — `otherLabel="x"` komt binnen als `otherlabel`. Attribuut-lookups in plugin.js moeten dus beide spellings accepteren (`attrs.otherLabel || attrs.otherlabel`) of meteen lowercase key gebruiken. camelCase-attrs zijn een stille undefined, geen error.

## Tag hygiene: nooit een gepubliceerde tag verplaatsen

Een tag met een GitHub Release eraan is immutabel. Post-release fix = patch-bump (1.1.0 blijft staan, fix wordt 1.1.1). De v1.1.0-tag is tweemaal geforceerd verplaatst tijdens de release — niet herhalen; release.sh doet tag/validate/release pas na render-verificatie.

## Release flow v2 (nov 2026) — epyc is de build-host

Projectfolder op de epyc: `~/projects/followup-chips/` — daarin `hermes-plugin-followup-chips/` (de repo), `hermes-agent-catalog/` (shallow clone van upstream voor de pin) en `release.sh` (bump → validate → push → catalog-branch → PR; gh staat in `~/.local/bin`, token via `gh auth login --with-token`). Windows blijft render/test-host: na elke release `cp` plugin.js naar `%LOCALAPPDATA%/hermes/desktop-plugins/followup-chips/` + Reload desktop plugins. v1.1.0: repo `6aff2a1`, pin-PR #157831 (netjes 1 commit, MERGEABLE), tag `v1.1.0`. Fork-main is sterk achter upstream — release.sh brancht daarom vanaf `origin/main` van upstream, niet van de fork.

## Contest submission (Nov 2026) — MERGED 🎉

PR #154186 MERGED 12 nov 10:59 UTC door Nous in main. Plugin nu officieel catalog-listed: plugin-catalog/followup-chips.yaml op main (pins 3e44fa9, maintainer nuonrg). Installeerbaar via hermes plugins install followup-chips; docs-pagina /docs/plugins/followup-chips genereren automatisch. Repo github.com/nuonrg/hermes-plugin-followup-chips. Tweet https://x.com/nuonrg/status/2120688594129973467, form ingevuld. Contest: late entry, uitslag afwachten.

## Catalog repo layout (submission doc)

Pinned tree MUST have `plugin.yaml` manifest (name/label/version/author/homepage/description/tags — cf hermes-official-plugins/accent-picker) + entrypoint at `desktop/plugin.js`. Validate first: `hermes plugins validate <dir> --install-deps`. PR adds ONE file `plugin-catalog/<name>.yaml` to NousResearch/hermes-agent; fork+branch, never direct push.