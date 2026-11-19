# Changelog

All notable changes to followup-chips are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/); dates in Europe/Amsterdam.

## [1.1.0] - 2026-11-19

### Added
- `title` attr: optional label above the chips — next-steps / follow-up question lists now render as the directive instead of prose
- `other="true"`: opt-in free-text row below the chips (Enter sends the text as the next turn) — for a remark that is not a chip
- `otherLabel` attr: custom placeholder for the free-text row (language-neutral, defaults to `…`)

### Fixed
- `otherLabel` placeholder crashed the contrib boundary (`ReferenceError: attrs is not defined`); the label now arrives via `props` and also works combined with `title`

## [1.0.0] - 2026-11-12

### Added
- `::followups{q1..qN}` transcript directive: clickable question chips under assistant replies; clicking sends the question as the next turn
- Hermes `arc-border` hover idiom; arc runs while the agent answers, rests on ✓ once chosen
- Per-block choice state (`<sessionId>::<source>`), persisted via `ctx.storage` across reloads
- Single-block `running` state: only the most recent choice animates
- First release in the plugin catalog (`plugin-catalog/followup-chips.yaml`, pin `3e44fa9`)
