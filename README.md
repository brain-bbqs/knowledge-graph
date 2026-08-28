# BRAIN BBQS Knowledge Graph

**Live site:** `https://brain-bbqs.github.io/knowledge-graph/`

---

## The schema file

Everything about the knowledge graph's structure lives in one file: **`schema.yaml`**.

Edit it to change what types of things exist in the graph, what properties they have, how they connect, and what the provenance layers mean. You never need to touch Python or RDF syntax.

---

## What's in schema.yaml

### `prefixes`
Short aliases for RDF namespaces. You probably won't need to touch this.

### `named_graphs`
The five containers that hold different kinds of data:

| Graph | What it holds |
|---|---|
| `core` | Canonical facts — names, affiliations, titles |
| `claims` | L2 curation status and L1 evidence links |
| `derived` | Computed edges (e.g. ORCID-matched authorship) |
| `access` | L3 security labels and access policies |
| `provenance` | Who ingested each record and when |

### `node_types`
The categories of things in the graph: **Person**, **Publication**, **WorkingGroup**, **Organization**.

Each node type lists its properties. A property looks like this:

```yaml
- predicate: "schema:name"
  label:      "Full Name"
  required:   true
  csv_column: name
```

- `predicate` — the RDF property (don't change unless you know what you're doing)
- `label` — human-readable name shown in the visualization
- `csv_column` — which column in the CSV holds this value
- `required` — whether the field must be present

### `edge_types`
Relationships between node types — e.g. Person → WorkingGroup, Person → Publication.

### `claim_schema`
Fields that track how confident we are in each assertion (L1 evidence, L2 curation status, confidence score, curator notes).

### `access_schema`
Security labels (`Internal`, `Public`) and access policies that control who can see what (L3).

---

## How to add a new property to Person

1. Open `schema.yaml`
2. Find the `Person:` node type → `properties:` list
3. Add a new entry, e.g.:

```yaml
- predicate: "ex:lab"
  label:      "Lab"
  csv_column: lab_name
```

4. Add the corresponding column to `people.csv`
5. Commit to `main` — the GitHub Action regenerates the graph automatically

---

## Files

| File | Purpose |
|---|---|
| `schema.yaml` | **The schema** — edit this to change the graph structure |
| `config.yaml` | Curator overlay — claim status, manual authorship links, security overrides |
| `people.csv` | Source data: consortium members |
| `publications.csv` | Source data: publications |
| `generate_kg.py` | Reads schema + CSVs + config → writes `kg.trig` |
| `kg.trig` | Generated RDF — do not edit directly |
| `index.html` | The visualization (Graph tab + Schema tab) |
