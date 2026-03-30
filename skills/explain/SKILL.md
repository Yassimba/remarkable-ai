---
name: explain
description: >
  Let the user explain a concept by drawing on their reMarkable tablet.
  Creates a blank page on the tablet, waits for the user to draw, then
  fetches and interprets the drawing.

  Use when the user says "let me draw this", "I'll sketch it out", "/explain",
  "let me show you", "I want to draw something", "let me explain on the
  tablet", "I'll whiteboard it", or wants to visually communicate an idea.
  Also suggest this when a text-based back-and-forth is going in circles —
  offer "Want to sketch it on your reMarkable? Sometimes drawing is faster."
---

# Explain (User draws, Claude reads)

The user draws on their reMarkable tablet. Claude fetches the drawing
and interprets it — identifying shapes, arrows, labels, and mapping
them to the concepts being discussed.

## Process

### 1. Create a blank page

Ask what the topic is (if not already clear from context), then push
a titled blank page:

```bash
remarkable-ai blank "Topic Name"
```

The title becomes the filename slug on the tablet. Use short, descriptive
titles — "Auth Flow" not "Authentication and Authorization Flow Diagram".

Tell the user: "Blank page is on your reMarkable in /AI Brainstorm/.
Draw your explanation and tell me when you're done."

### 2. Wait for the user to draw

The user draws on the tablet. Proceed when they signal they're done —
"done", "ok", "check it", "fetch it", "ready", "take a look", etc.

### 3. Fetch and render

```bash
remarkable-ai fetch "{topic-name}" --output /tmp/{topic}-explained.pdf
```

The topic name must match what you passed to `blank`. If the fetch fails
with "not found", the tablet may not have synced yet — tell the user
to open the document on the tablet (forces sync) and try again in a
few seconds.

### 4. Interpret the drawing

Read the rendered PDF with the Read tool. Be concrete about what you see:

- Name each shape you see and what's written in/near it
- Trace arrows and say what you think the connections mean
- Note spatial groupings — things drawn close together are related
- Flag anything you can't read and ask about it

Frame your interpretation as questions, not statements:

> "I see three boxes — 'API', 'Queue', 'Worker' — with arrows going
> left to right. The arrow from API to Queue is labeled 'enqueue'.
> I read this as: API pushes jobs onto a queue, workers pull them.
> Is that right?"

This lets the user correct you without having to re-explain everything.

### 5. Iterate

If the user wants to add more or correct your interpretation:
- They draw more on the same page on the tablet
- They say "check again" or "re-fetch"
- You re-fetch and re-interpret, noting what changed

Each round builds on the previous understanding. Reference earlier
interpretations: "Last time I saw X, now there's also Y — does Y
replace X or work alongside it?"
