# remarkable-ai

A CLI that bridges Claude Code and a reMarkable tablet. Push diagrams,
draw on them with a pen, pull the annotations back as a PDF.

```
┌─────────┐  push   ┌───────────┐  draw   ┌─────────┐
│ SVG/PDF ├────────▶│ reMarkable├────────▶│ .rmdoc  │
└─────────┘         └───────────┘         └────┬────┘
                                               │ fetch
                                          ┌────▼────┐
                                          │annotated│
                                          │  PDF    │
                                          └─────────┘
```

## Install

```bash
uv tool install remarkable-ai
```

You also need the [`remark`](https://github.com/ddvk/rmapi) CLI
(Go binary) authenticated with your reMarkable cloud account:

```bash
go install github.com/ddvk/rmapi@latest
rmapi  # follow the auth prompt once
```

## Commands

```bash
# Push a PDF or SVG to the tablet (SVGs auto-convert to PDF)
remarkable-ai push architecture.pdf
remarkable-ai push diagram.svg

# Fetch an annotated document — renders handwriting onto the original PDF
remarkable-ai fetch architecture --output annotated.pdf

# Create a blank titled page for freehand drawing
remarkable-ai blank "Neural Networks"

# Convert SVG to PNG (for review) or PDF
remarkable-ai render diagram.svg
remarkable-ai render diagram.svg --pdf --push-to-tablet

# Push a 9-point crosshair grid, then solve the coordinate transform
remarkable-ai calibrate

# List files on the tablet
remarkable-ai list
```

Everything lands in `/AI Brainstorm/` by default. Pass `--folder` to change it.

## How the fetch pipeline works

When you `fetch`, three things happen:

1. **Download** — `remark get` pulls the `.rmdoc` archive from the cloud
2. **Extract** — the archive is a ZIP with the original PDF and `.rm` binary
   annotation files; we parse the pen strokes out of the `.rm` with
   [rmscene](https://github.com/ricklupton/rmscene)
3. **Render** — each stroke is drawn onto a transparent PDF overlay (reportlab),
   then merged onto page 1 of the original (pypdf)

The coordinate mapping comes from a calibrated affine transform. Run
`remarkable-ai calibrate` once — circle each crosshair on the tablet, fetch
it back, and the least-squares solver fits the transform.

## Architecture

```
src/remarkable_ai/
├── core/                 # Domain types and the transport port. No deps.
│   ├── types.py          # PenColor, Point, Stroke, CalibrationTransform
│   ├── transport.py      # CloudTransport ABC
│   ├── errors.py         # CLIError → RemarkableError, SvgConversionError
│   └── constants.py      # Page dimensions (1152×936)
├── adapters/             # Talks to external tools. Depends on core only.
│   ├── remark_cli.py     # RemarkCLIAdapter — shells out to remark
│   ├── in_memory.py      # InMemoryAdapter — fake transport for tests
│   ├── renderer.py       # .rm parsing + PDF overlay compositing
│   ├── svg.py            # SVG→PNG/PDF (rsvg → cairosvg → Inkscape)
│   └── templates.py      # Blank page + calibration grid PDFs
└── cli/                  # The remarkable-ai command. Depends on both.
    ├── __init__.py       # App, console, error handling, entry point
    └── commands.py       # push, fetch, list, blank, render, calibrate
```

Boundaries are enforced by [tach](https://github.com/gauge-sh/tach) —
`core` never imports from `adapters` or `cli`.

## Claude Code skills

Three skills use this CLI to turn a conversation into a whiteboard session.
Copy the `skills/` directory into your project's `.claude/skills/` to use them.

### `/explain-me` — Claude draws, you read

Claude generates an SVG diagram explaining a concept, self-reviews it
by rendering to PNG and checking for overlaps/alignment, then pushes the
final version to your tablet.

### `/explain` — you draw, Claude reads

Creates a blank page on the tablet. You sketch your idea with the pen.
Claude fetches it back and interprets the drawing — identifies shapes,
arrows, labels, and maps them to technical concepts.

### `/architect` — collaborative architecture design

Given a plan, Claude proposes a hexagonal architecture with an ASCII tree,
a detail table, and a draw.io diagram pushed to the tablet. You annotate
with the pen. Claude fetches your notes and argues back from architecture
principles. Iterate until you agree.

## Development

```bash
git clone https://github.com/yassineim/remarkable-ai
cd remarkable-ai
uv sync --all-extras

# Quality gates
uv run ruff check src/          # lint
uv run ruff format --check src/ # format
uv run tach check               # boundary enforcement
uv run complexipy src/          # complexity (max 15)
```

## License

MIT
