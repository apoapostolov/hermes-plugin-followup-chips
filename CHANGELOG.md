# Changelog

Alle noemenswaardige wijzigingen in followup-chips worden hier gedocumenteerd.
Formaat gebaseerd op [Keep a Changelog](https://keepachangelog.com/); datums in Europe/Amsterdam.

## [1.1.0] - 2026-11-19

### Added
- `title`-attr: optioneel label boven de chips — vervolgstappen-/vervolgvragenlijsten renderen nu als directive in plaats van proza
- `other="true"`: opt-in vrij-tekstrij onder de chips (Enter verstuurt de tekst als volgende turn) — voor een opmerking die geen chip is
- `otherLabel`-attr: eigen placeholder voor de vrij-tekstrij (taalneutraal, default `…`)

### Fixed
- `otherLabel`-placeholder crashte de contrib-boundary (`ReferenceError: attrs is not defined`); label komt nu via `props` en werkt ook in combinatie met `title`

## [1.0.0] - 2026-11-12

### Added
- `::followups{q1..qN}` transcript-directive: klikbare vraagchips onder assistant-antwoorden; click verstuurt de vraag als volgende turn
- Hermes `arc-border` hover-idiem; arc draait tijdens het antwoorden, rust op ✓ bij keuze
- Keuzestate per blok (`<sessionId>::<source>`), persistiert via `ctx.storage` over reloads
- Enkel-blok `running`-state: alleen de nieuwste keuze animeert
- Eerste release in de plugin-catalog (`plugin-catalog/followup-chips.yaml`, pin `3e44fa9`)
