# Earth Trend Detective — design

Visual world: **field notebook** (chosen by the team, 2026-11-14). The app is an
Operate surface (a dashboard people work in), so the identity lives in precise
details, not decoration.

## Themes

Follows the operating system; the header button switches light/dark and the
choice is remembered (`src/lib/theme.ts`).

| Role | Light ("paper") | Dark ("night desk") |
|---|---|---|
| Page | warm paper `oklch(0.955 0.017 85)` | brown-black `oklch(0.185 0.008 70)` |
| Card | `oklch(0.985 0.008 85)` | `oklch(0.225 0.01 70)` |
| Text | ink `oklch(0.24 0.01 75)` | paper `oklch(0.93 0.015 85)` |
| Brand (selection, focus, current tab) | ink | paper |

All tokens live in `src/index.css`. Components never hard-code colours.

## Data colours

Okabe-Ito, colour-blind safe, and never reused for UI chrome:
`--trend-up` (orange), `--trend-down` (blue), `--trend-flat` (grey),
`--region-a` (pink), `--region-b` (green). Each trend colour has a `*-text`
shade that keeps text at ≥ 4.5:1 in both themes. Direction is always also
written in words and shown with an arrow.

## Type

- Headings (app title, card titles, region names): **Source Serif 4**
- Interface and body: **IBM Plex Sans**
- Numbers in KPI tiles and chart tooltips: **IBM Plex Mono** (data only, not labels)

Fonts are self-hosted through `@fontsource` packages (no requests to Google).

## Shape and density

Soft corners (`--radius: 0.75rem`), airy spacing, 40 px navigation targets,
≥ 24 px for every other control.
