---
name: explain-me
description: >
  Claude explains a concept visually by generating an SVG diagram, reviewing
  it for quality, and pushing it to the user's reMarkable tablet.

  Use when the user says "explain this to me", "draw me a diagram", "show me
  how this works", "/explain-me", "visualize this", "can you draw that", or
  when a concept would be clearer as a picture than as text. Also use
  proactively when explaining complex flows, data pipelines, state machines,
  or architecture — offer "Want me to draw this on your reMarkable?" whenever
  a wall of text isn't cutting it. If the user asks for a visual explanation
  of anything, this is the skill. Even if they don't mention the tablet — if
  they want a diagram, use this.
---

# Explain Me (Claude draws, user reads)

Generate a visual explanation as SVG, self-review it by rendering to PNG,
then push the final version to the user's reMarkable tablet.

## Process

### 1. Figure out what to draw

If the concept isn't clear, ask. Then pick the visual form that fits:

- **Flow diagram** — processes, pipelines, request lifecycles
- **Boxes and arrows** — architecture, dependencies, module relationships
- **Sequence diagram** — interactions over time, API call chains
- **Grid or table** — comparisons, feature matrices, tradeoff analysis
- **Annotated code** — algorithms, data structures, state transitions
- **Tree** — hierarchies, file structures, inheritance

Go with the simplest form that captures the idea. A 4-box flow beats
a 20-box architecture diagram if the concept is "how does auth work."

### 2. Generate the SVG

Write SVG directly — it gives precise control over layout.

E-ink readability rules (the reMarkable has no backlight and low contrast):

- `viewBox="0 0 1152 936"` — matches reMarkable landscape and draw.io default
- White or light background
- Dark strokes only (black or dark gray) — the tablet has no color
- Minimum **2px** stroke-width
- Minimum **14px** font size (16-18px is better for labels)
- `font-family="Helvetica, Arial, sans-serif"`
- Differentiate elements with stroke styles (solid, dashed, dotted) not color
- Label every shape and arrow — nothing unlabeled

Save to `/tmp/{topic}-explanation.svg`.

### 3. Self-review loop

Render the SVG to PNG, visually inspect it, fix issues. This catches
problems that are invisible in raw SVG (overlap, alignment, clipping).

```
REPEAT (max 4 iterations):
  1. remarkable-ai render /tmp/{topic}-explanation.svg
  2. Read the generated PNG with the Read tool
  3. Check for:
     - Text overlapping other text or shapes
     - Arrows crossing through boxes instead of around them
     - Labels cut off at edges of the viewBox
     - Uneven spacing or misaligned elements
     - Text too small to read at e-ink resolution
     - Missing labels on shapes or arrows
     - Broken arrowheads (marker-end not rendering)
  4. If any issue → fix the SVG, go to 1
  5. If clean → break
```

The first render almost always has overlap or spacing issues. Two to
three rounds is normal. If you hit 4 and it's still messy, simplify
the diagram — too many elements is the root cause.

### 4. Push to the tablet

```bash
remarkable-ai render /tmp/{topic}-explanation.svg --push-to-tablet
```

Tell the user what you sent: "'{topic}' is on your reMarkable."

### 5. Follow up

Briefly describe what the diagram shows so the user has context before
picking up the tablet. Keep it to 2-3 sentences — the diagram should
speak for itself.

If they want changes, edit the SVG and re-push. No need to re-run the
full review loop for small tweaks — just render, eyeball, push.
