# BRAIN BBQS Knowledge Graph

Interactive visualization of the consortium knowledge graph — people, publications, and working groups — with full L1/L2/L3 provenance layers.

---

## Curator workflow 

**Edit `config.yaml` → commit to main → `kg.trig` updates automatically.**

That's it. You never need to touch Turtle syntax or run any scripts.

### 1. Set a claim status

Open `config.yaml` on GitHub, find the person's email, and fill in `claim_status`:

```yaml
people:
  abigayle.fogarty@mssm.edu:
    claim_status: Verified    # Verified | Pending | Disputed | Retracted
    confidence: 0.95
    notes: "Confirmed member via email 2026-08"
```

### 2. Add a manual authorship link

A paper isn't linked to someone because their ORCID wasn't in the publications data?
Add it under `authorship:` using the PubMed ID and the person's email:

```yaml
authorship:
  - pmid: "39680425"
    person_email: "ds5577@nyu.edu"
    claim_status: Pending
    evidence: "https://doi.org/10.7554/eLife.93754"
```

### 3. Change a security label

Override someone's default `Internal` label to `Public`:

```yaml
security:
  "some.person@example.com":
    label: Public
    policy: policy-public-read
```

### What happens next

A GitHub Action (`update-kg.yml`) fires on every push to `main` that touches `config.yaml`. It runs `generate_kg.py`, which merges your YAML overlay with `people.csv` and `publications.csv` into a fresh `kg.trig`, then auto-commits it. GitHub Pages picks up the new TriG on the next page load.

---

## Named graph layers

```
graph:core       → canonical facts (names, affiliations, titles, etc.)
graph:claims     → L2 claim status + confidence + L1 evidence links
graph:derived    → authorship edges (ORCID-matched + manual from config.yaml)
graph:access     → L3 security labels and access policies
graph:provenance → ingestion provenance (agent, timestamps)
```

---

## Files

| File | Purpose |
|---|---|
| `config.yaml` | **Edit this** — curator overlay for claims, authorship, security |
| `index.html` | Interactive D3 + N3.js visualization (auto-loads kg.trig) |
| `kg.trig` | Generated TriG knowledge graph — do not edit directly |
| `people.csv` | Source: consortium members roster |
| `publications.csv` | Source: publications from Crossref ingestion |
| `generate_kg.py` | Lifter: merges CSVs + config.yaml → kg.trig |
| `.github/workflows/update-kg.yml` | GitHub Action that regenerates kg.trig on push |

---

## Local development

```bash
pip install pyyaml
python3 generate_kg.py          # regenerate kg.trig
python3 -m http.server 8080     # serve locally (fetch() needs HTTP)
# open http://localhost:8080
```
