"""CLI tool for pushing diagrams to a reMarkable tablet and pulling back annotated drawings as PDFs.

Built for AI-human collaboration: Claude Code generates a diagram,
pushes it to the tablet, the human sketches on it, then the tool
fetches the annotations and renders them back onto the original PDF.

    ┌─────────┐  push   ┌───────────┐  draw   ┌─────────┐
    │ SVG/PDF ├────────▶│ reMarkable├────────▶│ .rmdoc  │
    └─────────┘         └───────────┘         └────┬────┘
                                                   │ fetch
                                              ┌────▼────┐
                                              │ annotated│
                                              │   PDF    │
                                              └─────────┘

Package layout::

    core/       Domain types and the CloudTransport port. No deps.
    adapters/   Talks to external tools: remark CLI, rsvg, reportlab.
    cli/        The ``remarkable-ai`` command. Wires adapters together.
"""
