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

## Quickstart

```bash
pip install remarkable-ai
remarkable-ai setup
```

That's it. `setup` downloads the [remark](https://github.com/ddvk/rmapi)
binary for your platform and walks you through cloud auth. No Go
toolchain needed.

## Commands

```bash
remarkable-ai setup                        # download remark + authenticate
remarkable-ai push architecture.pdf        # upload PDF to tablet
remarkable-ai push diagram.svg             # auto-converts SVG to PDF first
remarkable-ai fetch architecture           # pull annotated doc, render strokes onto PDF
remarkable-ai blank "Neural Networks"      # push a titled blank page for drawing
remarkable-ai render diagram.svg           # SVG to PNG (for review)
remarkable-ai render diagram.svg --pdf --push-to-tablet
remarkable-ai calibrate                    # push 9-point grid for coordinate alignment
remarkable-ai list                         # list files on tablet
```

All commands default to the `/AI Brainstorm/` folder. Pass `--folder` to change it.

## How fetch works

```
.rmdoc archive          .rm binary             annotated PDF
┌────────────┐     ┌──────────────┐     ┌───────────────────┐
│ diagram.pdf│     │ SceneLineItem│     │ original PDF      │
│ *.rm files │────▶│  → Stroke[]  │────▶│ + stroke overlay  │
└────────────┘     └──────────────┘     └───────────────────┘
  extract_strokes    parse_strokes        render_annotations
                     _from_rm
```

1. `remark get` pulls the `.rmdoc` archive from the cloud
2. The archive is a ZIP with the original PDF and `.rm` annotation layers.
   [rmscene](https://github.com/ricklupton/rmscene) parses the pen strokes.
3. Each stroke lands on a transparent PDF overlay (reportlab), merged onto
   page 1 of the original (pypdf)

The coordinate mapping comes from a calibrated affine transform. Run
`remarkable-ai calibrate` once, circle each crosshair on the tablet,
fetch it back. The transform solves from there.

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
│   ├── templates.py      # Blank page + calibration grid PDFs
│   └── setup.py          # Binary download + install
└── cli/                  # Wires adapters together.
    ├── __init__.py       # App, console, error handling, entry point
    └── commands.py       # setup, push, fetch, list, blank, render, calibrate
```

Boundaries enforced by [tach](https://github.com/gauge-sh/tach) —
`core` never imports from `adapters` or `cli`.

## Claude Code skills

Three skills in the `skills/` directory turn a conversation into a
whiteboard session. Copy them to your project's `.claude/skills/`.

**`/explain-me`** — Claude draws, you read. Generates an SVG diagram,
self-reviews it by rendering to PNG, then pushes the final version to
your tablet.

**`/explain`** — You draw, Claude reads. Pushes a blank page to the
tablet. You sketch with the pen. Claude fetches it back and interprets
the drawing.

**`/architect`** — Collaborative architecture design. Claude proposes
structure (any style — hexagonal, layered, flat, whatever fits), pushes
a diagram to the tablet. You annotate with the pen. Claude fetches your
notes and argues back from principles. Repeat until you agree.

## Development

```bash
git clone https://github.com/Yassimba/remarkable-ai
cd remarkable-ai
uv sync --all-extras

uv run ruff check src/          # lint
uv run ruff format --check src/ # format
uv run tach check               # boundary enforcement
uv run complexipy src/          # complexity (max 15)
```

## License

MIT
