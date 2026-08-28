# BRAIN BBQS Knowledge Graph · GitHub Pages

Interactive visualization of the consortium knowledge graph — people, publications, and working groups — with full L1/L2/L3 provenance layers.

**Live site:** `https://brain-bbqs.github.io/knowledge-graph/`

---

## Files

| File | Purpose |
|---|---|
| `index.html` | Interactive D3 + N3.js visualization |
| `kg.trig` | TriG knowledge graph (5 named graphs) |
| `people.csv` | Source: consortium members roster |
| `publications.csv` | Source: publications from Crossref ingestion |
| `generate_kg.py` | Regenerates `kg.trig` from the two CSVs |

---

## How to edit the graph (for curators)

The file to edit is **`kg.trig`**. You can edit it directly via the GitHub web UI (click the pencil icon on the file), or clone the repo and open it in any text editor.

### Named graph layers

```
graph:core       → canonical facts (names, affiliations, titles, etc.)
graph:claims     → L2 claim status + confidence + L1 evidence links
graph:derived    → computed authorship edges (person → publication, ORCID-matched)
graph:access     → L3 security labels and access policies
graph:provenance → ingestion provenance (agent, timestamps)
```

### Updating a claim (L2)

Find the claim in `graph:claims { … }`. Each claim looks like:

```turtle
claim:identity-25b356ed
  a ex:Claim ;
  ex:subject person:25b356ed-4392-46ab-a8ae-723007fb9820 ;
  ex:predicate schema:name ;
  ex:claimStatus "Verified" ;        ← change this
  ex:confidence "0.95"^^xsd:decimal . ← and/or this
```

Valid `ex:claimStatus` values: `"Verified"`, `"Disputed"`, `"Pending"`, `"Retracted"`.

### Updating a security label (L3)

Find the entity in `graph:access { … }`:

```turtle
person:25b356ed-4392-46ab-a8ae-723007fb9820
  ex:securityLabel "Internal" ;      ← "Internal" or "Public"
  ex:accessPolicy  "policy-consortium-read" .
```

### Adding an authorship edge manually

In `graph:derived { … }`, add a line:

```turtle
person:<person_id> schema:author pub:<publication_id> .
```

And add the matching claim in `graph:claims { … }`:

```turtle
claim:authorship-<8-char-pub-id>-<orcid-slug>
  a ex:Claim ;
  ex:subject person:<person_id> ;
  ex:predicate schema:author ;
  ex:object pub:<publication_id> ;
  ex:claimStatus "Pending" ;
  ex:hasEvidence [ dct:source <https://doi.org/...> ] .
```

---

## Regenerating `kg.trig` from updated CSVs

```bash
python3 generate_kg.py
```

This reads `people.csv` and `publications.csv` and overwrites `kg.trig`.

---

## Local development

```bash
# Serve locally (needed because fetch() requires HTTP, not file://)
python3 -m http.server 8080
# then open http://localhost:8080
```
