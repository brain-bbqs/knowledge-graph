# Unstructured Data Sources

Raw, unprocessed source material that feeds into `knowledge-graph.ttl`.

Each subdirectory corresponds to a node or category in the knowledge graph. Drop documents (PDFs, markdown, text, slide decks) into the appropriate folder. Claude will parse and extract triples from this material to populate the TTL.

## Structure

```
unstructured_data/
├── working_groups/     # Source docs per working group
├── events/             # Agendas, notes, recordings metadata per event
└── projects/           # Per-project abstracts and claims
    └── <project>/
        ├── abstract/   # Project abstract / overview documents
        └── claims/     # Specific claims, results, outputs
```
