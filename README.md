# BRAIN BBQS Knowledge Graph

Interactive force-directed visualization of the [BRAIN Behavior Quantification and Synchronization](https://brain-bbqs.org/) consortium — working groups, chairs, projects, products, events, and announcements.

## Files

| File | Purpose |
|------|---------|
| `knowledge-graph.ttl` | RDF/Turtle data — edit this to add or update nodes and relationships |
| `index.html` | Self-contained visualization (D3 + N3.js, no build step) |
| `.nojekyll` | Tells GitHub Pages to serve `.ttl` files as-is |

## Editing the graph

Open `knowledge-graph.ttl` and add or modify nodes following the existing patterns:

```turtle
bbqs:my-new-node a ex:Product ;          # type drives color + size
    schema:name        "My Tool" ;
    schema:description "What it does" ;
    schema:isPartOf    bbqs:wg-analytics . # edge to parent node
```

**Node types and colors**

| Type | Color |
|------|-------|
| `ex:Consortium` | orange-brown |
| `ex:WorkingGroup` | blue |
| `schema:Person` | green |
| `ex:Project` | purple |
| `schema:MonetaryGrant` | gold |
| `ex:Announcement` | red-orange |
| `schema:Event` | teal |
| `ex:Product` | slate |

## Local preview

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

## Live site

https://brain-bbqs.github.io/knowledge-graph/
