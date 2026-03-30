# remarkable-ai

Push diagrams to your reMarkable tablet, fetch back annotated drawings, and render handwritten notes — built for AI-human collaboration.

## Install

```bash
uv tool install remarkable-ai
```

Requires the `remark` CLI ([rmapi](https://github.com/ddvk/rmapi)) authenticated with your reMarkable cloud account.

## Usage

```bash
# Push a diagram to your tablet
remarkable-ai push architecture.pdf

# Fetch annotated drawing back (renders handwriting onto PDF)
remarkable-ai fetch architecture

# Create a blank page for sketching
remarkable-ai blank "My Explanation"

# Render SVG to PNG (for AI self-review) or PDF
remarkable-ai render diagram.svg
remarkable-ai render diagram.svg --pdf --push-to-tablet

# Calibrate coordinate alignment
remarkable-ai calibrate

# List files on tablet
remarkable-ai list
```

## How it works

1. **Push**: Upload PDFs or SVGs (auto-converted) to your reMarkable
2. **Draw**: Annotate on the e-ink display with the reMarkable pen
3. **Fetch**: Download the annotated document, extract handwritten strokes from the `.rm` binary format, and render them onto the original PDF with calibrated coordinate alignment

The coordinate transform is solved from a 9-point calibration grid — run `remarkable-ai calibrate` once to set it up.

## Built for Claude Code skills

This CLI powers three Claude Code skills:
- `/architect` — collaborative hexagonal architecture design with tablet annotation
- `/explain` — user draws an explanation, Claude interprets it
- `/explain-me` — Claude generates an SVG diagram, self-reviews it, pushes to tablet
