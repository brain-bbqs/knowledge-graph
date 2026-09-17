# BRAIN BBQS Knowledge Graph — AI Collaboration Constitution

This document defines the responsibilities of the two AI collaborators working on this repository. It exists so each agent knows its lane, avoids conflicting edits, and hands off cleanly to the other.

---

## Claude (Anthropic)

**Role:** Back-end custodian and documentation lead.

**Owns:**
- `knowledge-graph.ttl` — the sole source of truth for graph data. All node additions, relationship changes, schema evolution, and RDF/schema.org decisions happen here.
- `README.md` — kept current whenever the data model or file structure changes.
- `CONSTITUTION.md` — this file.
- `.nojekyll` and any non-UI repository configuration.

**Responsibilities:**
- Add, update, and validate RDF triples in `knowledge-graph.ttl`.
- Evolve the schema (new `ex:` types, new schema.org properties, new relationship predicates) in response to real consortium data.
- Keep documentation accurate and in sync with the actual state of the repository.
- Pull `main` before every edit to avoid conflicting with Lovable's UI pushes.
- Never touch `index.html` unless explicitly instructed by the user.

**Does not:**
- Change visual design, colors, layout, or JavaScript behavior.
- Modify `index.html` unilaterally.

---

## Lovable

**Role:** Front-end and visualization lead.

**Owns:**
- `index.html` — the self-contained visualization page (D3 force graph, legend, search, details panel, styling).

**Responsibilities:**
- Improve and maintain the graph visualization, UI layout, interactivity, and styling.
- Keep the visualization compatible with the data model in `knowledge-graph.ttl` — specifically: node types used in `TYPE_COLORS` and `NODE_RADIUS` must match the `ex:` and `schema:` types defined in the TTL.
- Communicate to Claude (via the user) when the visualization needs a new node type or property exposed in the data.
- Never modify `knowledge-graph.ttl`, `README.md`, or `CONSTITUTION.md`.

**Does not:**
- Edit RDF data or schema definitions.
- Change documentation files.

---

## Shared rules

1. **`main` is the integration branch.** Both agents read from and merge into `main`. Neither force-pushes to `main`.
2. **Feature branches are per-agent.** Claude works on `claude/*` branches; Lovable works on its own branches. PRs merge to `main`.
3. **Data model changes require coordination.** If Lovable needs a new node type rendered (e.g. a new color for `ex:Tool`), it signals the user, who asks Claude to add the type to the TTL first. Lovable then adds the color/radius to `index.html`.
4. **No silent overwrites.** If either agent detects a conflict with the other's files, it stops and flags it to the user rather than overwriting.
5. **The TTL is authoritative.** If `index.html` and `knowledge-graph.ttl` disagree (e.g. a color key references a type that doesn't exist in the TTL), the TTL wins and the UI is updated to match.
