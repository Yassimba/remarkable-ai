# remarkable-ai

Push diagrams to a reMarkable tablet, draw on them with a pen,
pull the annotations back as a PDF.

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
uv tool install remarkable-ai
remarkable-ai setup
```

`setup` grabs the right binary for your platform and logs you into
your reMarkable cloud account. After that, you're good to go.

## Commands

```bash
remarkable-ai setup                        # one-time install + cloud login
remarkable-ai push architecture.pdf        # upload PDF to tablet
remarkable-ai push diagram.svg             # auto-converts SVG to PDF first
remarkable-ai fetch architecture           # pull annotated doc, render strokes onto PDF
remarkable-ai blank "Neural Networks"      # titled blank page for freehand drawing
remarkable-ai render diagram.svg           # SVG to PNG (quick review)
remarkable-ai render diagram.svg --pdf --push-to-tablet
remarkable-ai calibrate                    # 9-point grid for coordinate alignment
remarkable-ai list                         # list files on tablet
```

Files land in `/AI Brainstorm/` by default. `--folder` changes it.

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

The tablet saves pen strokes in a proprietary `.rm` binary format,
packed inside a `.rmdoc` ZIP alongside the original PDF.

`fetch` downloads that archive, parses the strokes with
[rmscene](https://github.com/ricklupton/rmscene), draws them onto
a transparent overlay, and merges the overlay onto page 1 of your
original PDF.

Strokes need a coordinate mapping so they land in the right spot.
Run `remarkable-ai calibrate` once — circle each crosshair on the
tablet, fetch it back, and the mapping calibrates itself.

## Architecture

```
src/remarkable_ai/
├── core/                 # Types and the transport port. No deps.
│   ├── types.py          # PenColor, Point, Stroke, CalibrationTransform
│   ├── transport.py      # CloudTransport ABC
│   ├── errors.py         # CLIError → RemarkableError, SvgConversionError
│   └── constants.py      # Page dimensions (1152×936)
├── adapters/             # External tools. Depends on core only.
│   ├── remark_cli.py     # RemarkCLIAdapter — cloud via subprocess
│   ├── in_memory.py      # InMemoryAdapter — fake transport for tests
│   ├── renderer.py       # .rm parsing + PDF compositing
│   ├── svg.py            # SVG→PNG/PDF (rsvg → cairosvg → Inkscape)
│   ├── templates.py      # Blank page + calibration grid
│   └── setup.py          # Binary download + install
└── cli/                  # Wires everything together.
    ├── __init__.py       # App, console, error handling
    └── commands.py       # setup, push, fetch, list, blank, render, calibrate
```

[tach](https://github.com/gauge-sh/tach) enforces the boundaries —
`core` can't import from `adapters` or `cli`.

## Claude Code skills

Three skills in `skills/` turn a conversation into a tablet
whiteboard session. Copy them into your project's `.claude/skills/`.

**`/explain-me`** — Claude draws, you read. Generates an SVG,
reviews it for overlap and alignment, pushes the clean version
to your tablet.

**`/explain`** — You draw, Claude reads. Puts a blank page on the
tablet. You sketch. Claude fetches it and tells you what it sees.

**`/architect`** — Design sessions. Claude proposes structure, pushes
a diagram. You scribble objections on the tablet. Claude fetches
your notes and argues back. Keep going until you agree.

## Development

```bash
git clone https://github.com/Yassimba/remarkable-ai
cd remarkable-ai
uv sync --all-extras

uv run ruff check src/          # lint
uv run ruff format --check src/ # format
uv run tach check               # boundaries
uv run complexipy src/          # complexity (max 15)
```

## License

MIT
