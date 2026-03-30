---
name: architect
description: >
  Collaborative architecture design sessions using a reMarkable tablet.
  Given a plan, feature doc, or just a conversation, propose an architecture,
  generate a diagram, push it to the tablet for annotation, pull back the
  user's handwritten notes, and iterate.

  Use when the user says "architect", "design the architecture", "where should
  this live", "/architect", "let's design this", "how should I structure this",
  "draw the architecture", or wants to figure out how to organize a system.
  Works with any architecture style — hexagonal, layered, clean architecture,
  modular monolith, microservices, or something custom. Also suggest this when
  a plan doc or feature spec exists but has no architecture section — offer
  "Want to design the architecture together on the tablet?"
---

# Architecture Design Session

Turn a plan into an architecture through collaborative debate on the
reMarkable tablet. You propose structure. The user annotates with a pen.
You pull back their notes and respond. Iterate until you agree.

## Process

### 1. Understand the system

Read the plan doc, feature spec, or conversation context. Identify:

- What are the main components or concepts?
- What are the external boundaries (APIs, databases, queues, users)?
- What are the key data flows?
- Are there existing patterns in the codebase to follow?

If working in an existing codebase, check the project structure first.
Match whatever style is already there — don't impose a new one.

### 2. Pick an architecture style

Either detect from the codebase or ask the user. Common styles:

| Style | When it fits | Key idea |
|-------|-------------|----------|
| **Flat/simple** | Small tools, scripts, CLIs | One package, files grouped by concept |
| **Layered** | CRUD apps, standard web services | Presentation → business → data |
| **Hexagonal** | Domain-heavy, many integrations | Core + ports + adapters |
| **Clean architecture** | Complex domains, testability focus | Entities → use cases → interface adapters → frameworks |
| **Modular monolith** | Large apps that might split later | Independent modules with clear boundaries |
| **Microservices** | Teams need independent deployment | Separate services per bounded context |

Don't default to the most complex option. A 500-line CLI doesn't need
hexagonal architecture. A CRUD API doesn't need microservices. Pick the
simplest style that handles the actual complexity.

If the user has a preference, use it.

### 3. Propose the architecture

Present in three formats in one message:

**ASCII tree** — for quick scanning in chat:
```
src/
├── api/
│   ├── routes.py       — HTTP endpoints
│   └── schemas.py      — request/response models
├── services/
│   ├── orders.py       — order business logic
│   └── payments.py     — payment processing
└── storage/
    ├── database.py     — SQLAlchemy models + queries
    └── cache.py        — Redis cache layer
```

Annotate each file with what it does and why it's in that directory.

**Detail table** — for completeness:

| Component | Location | Depends on | Why here |
|-----------|----------|------------|----------|
| OrderService | services/ | storage.database | Business logic, no HTTP knowledge |
| create_order | api/routes.py | services.orders | Thin HTTP handler, delegates to service |

The "Why here" column is the reasoning you'll defend when challenged.

**Diagram** — pushed to the tablet:

Generate a draw.io XML or SVG showing components, their boundaries,
and data flow. Convert to PDF and push:

```bash
remarkable-ai push /tmp/architecture.pdf
```

### 4. Collaborative debate

When the user says "move X to Y", "this doesn't belong here", or
annotates the diagram with arrows/circles/crossouts:

**Push back with reasoning before complying:**

1. State the principle behind the current placement
2. Explain what breaks or gets worse if you move it
3. If the user's reasoning is stronger, concede and update

```
User: "OrderValidator should be in api/, it validates request data"
You:  "OrderValidator checks business rules (minimum order amount,
      inventory availability) — that's domain logic, not HTTP
      validation. If it moves to api/, the service layer can't
      reuse it for CLI or queue-triggered orders.
      Counter-proposal: keep OrderValidator in services/, add a
      separate RequestSchema in api/ for HTTP-specific validation."
```

The point is to surface tradeoffs, not to be stubborn. If the user
says "just move it" after hearing the reasoning, do it.

### 5. Fetch annotations from the tablet

When the user says "check my notes", "fetch", or "take a look":

```bash
remarkable-ai fetch "{diagram-name}" --output /tmp/annotated-arch.pdf
```

Read the PDF. Interpret handwritten annotations:
- Arrows suggest "this should connect to that" or "data flows this way"
- Circles/underlines mean "pay attention to this"
- Crossouts mean "remove this" or "this is wrong"
- Written words near components are rename suggestions or notes

Respond to each annotation specifically.

### 6. Iterate

After each change:
1. Update the ASCII tree (full, not a diff — the user sees current state)
2. Re-generate and push the diagram
3. Update the detail table

### 7. Finalize

When the user says "looks good", "agreed", or "done":

1. Add an `## Architecture` section to the plan doc with the final
   ASCII tree and detail table
2. Save the diagram to `docs/architecture/`
3. Write a brief architecture doc explaining what lives where and
   the key decisions made during the session

## Principles to argue from

These apply regardless of architecture style:

**Dependencies flow one direction.** Pick a direction (outer → inner,
top → down, left → right) and enforce it. Circular dependencies are
a design problem, not something to work around with late imports.

**Group by concept, not by type.** `orders/service.py` is better than
`services/order_service.py` when the codebase has many concepts. But
for small projects, grouping by type is fine.

**Hide complexity behind simple interfaces.** If a module's interface
is as complex as its implementation, the boundary isn't earning its
keep. Deep modules with narrow APIs beat shallow wrappers.

**What changes together lives together.** If changing feature X always
means editing files A, B, and C, those files probably belong in the
same module.

**Adapters hide I/O, not logic.** Business rules belong in the domain
layer even if an adapter needs them. The adapter wraps infrastructure
(SQL, HTTP, files) around domain logic — it doesn't own the logic.

**Test at boundaries, not internals.** Good architecture makes testing
easier. If you need to mock 5 things to test one function, the design
has too many dependencies.
