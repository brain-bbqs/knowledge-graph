#!/usr/bin/env python3
"""Generate kg.trig from people.csv + publications.csv + config.yaml + schema.yaml."""

import csv, re, sys, os
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

def slug(s):
    return re.sub(r'[^A-Za-z0-9_-]', '_', s.strip())

def lit(val, dtype=None):
    if dtype:
        return f'"{esc(val)}"^^{dtype}'
    return f'"{esc(val)}"'

def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

# ── Load schema.yaml ──────────────────────────────────────────────────────────
schema = {}
if yaml and os.path.exists('schema.yaml'):
    with open('schema.yaml', encoding='utf-8') as f:
        schema = yaml.safe_load(f) or {}

FALLBACK_PREFIXES = """\
@prefix schema: <https://schema.org/> .
@prefix ex:     <https://brain-bbqs.org/vocab/> .
@prefix person: <https://brain-bbqs.org/person/> .
@prefix pub:    <https://brain-bbqs.org/pub/> .
@prefix org:    <https://brain-bbqs.org/org/> .
@prefix wg:     <https://brain-bbqs.org/wg/> .
@prefix claim:  <https://brain-bbqs.org/claim/> .
@prefix prov:   <http://www.w3.org/ns/prov#> .
@prefix dct:    <http://purl.org/dc/terms/> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .
@prefix graph:  <https://brain-bbqs.org/graph/> .

"""

schema_prefixes = schema.get('prefixes', {})
if schema_prefixes:
    lines = [f'@prefix {k}: <{v}> .' for k, v in schema_prefixes.items()]
    if 'graph' not in schema_prefixes:
        lines.append('@prefix graph: <https://brain-bbqs.org/graph/> .')
    PREFIXES = '\n'.join(lines) + '\n\n'
else:
    PREFIXES = FALLBACK_PREFIXES

node_types = schema.get('node_types', {})

# ── CSV data ──────────────────────────────────────────────────────────────────
people = read_csv('people.csv')
pubs   = read_csv('publications.csv')

# ── Load config.yaml overlay ──────────────────────────────────────────────────
config = {'people': {}, 'authorship': [], 'security': {}}
if yaml and os.path.exists('config.yaml'):
    with open('config.yaml', encoding='utf-8') as f:
        loaded = yaml.safe_load(f) or {}
    config['people']     = loaded.get('people', {}) or {}
    config['authorship'] = loaded.get('authorship', []) or []
    config['security']   = loaded.get('security', {}) or {}

cfg_by_email = {k.strip(): v for k, v in config['people'].items() if k and v}

orcid_map = {}
for p in people:
    if p['orcid'].strip():
        orcid_map[p['orcid'].strip()] = p['person_id'].strip()

pmid_to_pub = {r['pmid'].strip(): r for r in pubs if r['pmid'].strip()}
email_to_person_id = {r['email_primary'].strip(): r['person_id'].strip()
                      for r in people if r['email_primary'].strip()}

# ── Schema-driven property → triple generation ────────────────────────────────
def props_to_triples(row, prop_defs):
    """Generate Turtle predicate-object lines from a CSV row + schema property defs."""
    triples = []
    for prop in prop_defs:
        col = prop.get('csv_column')
        if not col:
            continue
        val = row.get(col, '').strip()
        if not val:
            continue
        pred      = prop['predicate']
        scheme    = prop.get('identifier_scheme')
        obj_t     = prop.get('object_type')
        multi     = prop.get('multi_value', False)
        sep       = prop.get('separator', ',')
        dtype     = prop.get('datatype')
        ref_style = prop.get('ref_style')  # 'iri' or 'blank'

        if scheme:
            triples.append(f'  ; {pred} [ schema:propertyID "{scheme}" ; schema:value {lit(val)} ]')
        elif obj_t:
            ot_def  = node_types.get(obj_t, {})
            iri_pfx = ot_def.get('iri_prefix', obj_t.lower())
            rdf_t   = prop.get('rdf_type') or ot_def.get('rdf_type') or f'schema:{obj_t}'
            # Use IRI ref when the object type is a named entity, unless explicitly blanked
            use_iri = (ref_style == 'iri') if ref_style else (
                ot_def.get('iri_prefix') and ref_style != 'blank'
            )
            # 'blank' ref_style overrides iri_prefix
            if ref_style == 'blank':
                use_iri = False
            if multi:
                for item in val.split(sep):
                    item = item.strip()
                    if item:
                        if use_iri:
                            triples.append(f'  ; {pred} {iri_pfx}:{slug(item)}')
                        else:
                            triples.append(f'  ; {pred} [ a {rdf_t} ; schema:name {lit(item)} ]')
            else:
                if use_iri:
                    triples.append(f'  ; {pred} {iri_pfx}:{slug(val)}')
                else:
                    triples.append(f'  ; {pred} [ a {rdf_t} ; schema:name {lit(val)} ]')
        elif multi:
            for item in val.split(sep):
                item = item.strip()
                if item:
                    triples.append(f'  ; {pred} {lit(item, dtype) if dtype else lit(item)}')
        elif dtype:
            triples.append(f'  ; {pred} {lit(val, dtype)}')
        else:
            triples.append(f'  ; {pred} {lit(val)}')
    return triples

# ── Node type config helpers ──────────────────────────────────────────────────
def nt_cfg(name, id_col_default, rdf_t_default, pfx_default):
    nt = node_types.get(name, {})
    return {
        'props':   nt.get('properties', []),
        'rdf_t':   nt.get('rdf_type', rdf_t_default),
        'pfx':     nt.get('iri_prefix', pfx_default),
        'id_col':  nt.get('id_column', id_col_default),
    }

per_nt  = nt_cfg('Person',      'person_id',      'schema:Person',           'person')
pub_nt  = nt_cfg('Publication', 'publication_id', 'schema:ScholarlyArticle', 'pub')
wg_nt   = nt_cfg('WorkingGroup', None,            'ex:WorkingGroup',          'wg')

# ─────────────────────────────────────────────────────────────────────────────
# graph:core  — canonical entities
# ─────────────────────────────────────────────────────────────────────────────
core_lines = []

for p in people:
    pid = p.get(per_nt['id_col'], '').strip()
    if not pid:
        continue
    triples = [f"  a {per_nt['rdf_t']}"] + props_to_triples(p, per_nt['props'])
    core_lines.append(f"{per_nt['pfx']}:{pid}\n" + "\n".join(triples) + " .\n")

for row in pubs:
    pub_id = row.get(pub_nt['id_col'], '').strip()
    if not pub_id:
        continue
    triples = [f"  a {pub_nt['rdf_t']}"] + props_to_triples(row, pub_nt['props'])
    core_lines.append(f"{pub_nt['pfx']}:{pub_id}\n" + "\n".join(triples) + " .\n")

# Working groups (synthesized from person membership lists)
wg_seen = set()
for p in people:
    for wg in p['working_groups'].split(';'):
        wg = wg.strip()
        if wg and wg not in wg_seen:
            wg_seen.add(wg)
            core_lines.append(
                f"{wg_nt['pfx']}:{slug(wg)}\n  a {wg_nt['rdf_t']} ; schema:name {lit(wg)} .\n"
            )

# ─────────────────────────────────────────────────────────────────────────────
# graph:derived — authorship edges (ORCID-matched + manual from config.yaml)
# ─────────────────────────────────────────────────────────────────────────────
derived_lines = []
authorship_claims = []

for row in pubs:
    pub_id = row.get(pub_nt['id_col'], '').strip()
    if not pub_id or not row['author_orcids'].strip():
        continue
    for orcid in [o.strip() for o in row['author_orcids'].split(';') if o.strip()]:
        if orcid in orcid_map:
            person_id = orcid_map[orcid]
            derived_lines.append(f"person:{person_id} schema:author pub:{pub_id} .")
            claim_id = f"authorship-{pub_id[:8]}-{slug(orcid)}"
            authorship_claims.append({
                'claim_id': claim_id,
                'person_id': person_id,
                'pub_id': pub_id,
                'orcid': orcid,
                'doi': row['doi'].strip(),
                'claim_status': row['claim_status'].strip() or
                    ('Verified' if row['doi'].strip() else ''),
                'confidence': row['confidence'].strip(),
                'evidence_source': row['evidence_source'].strip() or
                    (f"https://doi.org/{row['doi'].strip()}" if row['doi'].strip() else row['url'].strip()),
            })

for entry in config['authorship']:
    pmid  = str(entry.get('pmid', '')).strip()
    email = str(entry.get('person_email', '')).strip()
    if not pmid or not email:
        continue
    pub_row = pmid_to_pub.get(pmid)
    pid     = email_to_person_id.get(email)
    if not pub_row or not pid:
        print(f"  [config] WARNING: authorship entry not matched — pmid={pmid} email={email}", file=sys.stderr)
        continue
    pub_id   = pub_row[pub_nt['id_col']].strip()
    edge_key = f"person:{pid} schema:author pub:{pub_id}"
    if edge_key not in derived_lines:
        derived_lines.append(edge_key + " .")
    claim_id = f"authorship-{pub_id[:8]}-cfg-{slug(email)}"
    authorship_claims.append({
        'claim_id': claim_id,
        'person_id': pid,
        'pub_id': pub_id,
        'orcid': '',
        'doi': pub_row['doi'].strip(),
        'claim_status': str(entry.get('claim_status', 'Pending')),
        'confidence': str(entry.get('confidence', '')),
        'evidence_source': str(entry.get('evidence', pub_row['url'].strip())),
    })

# ─────────────────────────────────────────────────────────────────────────────
# graph:claims — reified Claim nodes (L1 + L2)
# ─────────────────────────────────────────────────────────────────────────────
claims_lines = []

for ac in authorship_claims:
    cid = ac['claim_id']
    triples = [
        '  a ex:Claim',
        f"  ; ex:subject person:{ac['person_id']}",
        '  ; ex:predicate schema:author',
        f"  ; ex:object pub:{ac['pub_id']}",
    ]
    if ac['claim_status']:
        triples.append(f"  ; ex:claimStatus {lit(ac['claim_status'])}")
    if ac['confidence']:
        triples.append(f"  ; ex:confidence {lit(ac['confidence'], 'xsd:decimal')}")
    if ac['evidence_source']:
        triples.append(f"  ; ex:hasEvidence [ dct:source <{ac['evidence_source']}> ]")
    claims_lines.append(f"claim:{cid}\n" + "\n".join(triples) + " .\n")

for p in people:
    pid   = p.get(per_nt['id_col'], '').strip()
    email = p['email_primary'].strip()
    if not pid:
        continue
    cid = f"identity-{pid[:8]}"
    cfg = cfg_by_email.get(email, {}) or {}
    claim_status   = str(cfg.get('claim_status', '') or p['claim_status'].strip()).strip()
    confidence_val = str(cfg.get('confidence',   '') or p['confidence'].strip()).strip()
    evidence_src   = p['evidence_source'].strip()
    asserted_in    = p['asserted_in'].strip()
    notes_val      = str(cfg.get('notes', '') or '').strip()

    triples = [
        '  a ex:Claim',
        f"  ; ex:subject person:{pid}",
        '  ; ex:predicate schema:name',
    ]
    if claim_status:
        triples.append(f"  ; ex:claimStatus {lit(claim_status)}")
    if confidence_val:
        triples.append(f"  ; ex:confidence {lit(confidence_val, 'xsd:decimal')}")
    if evidence_src:
        triples.append(f"  ; ex:hasEvidence [ dct:source <{evidence_src}> ]")
    if asserted_in:
        triples.append(f"  ; ex:assertedIn {lit(asserted_in)}")
    if notes_val:
        triples.append(f"  ; ex:curatorNote {lit(notes_val)}")
    claims_lines.append(f"claim:{cid}\n" + "\n".join(triples) + " .\n")

# ─────────────────────────────────────────────────────────────────────────────
# graph:access — L3 security labels + access policies
# ─────────────────────────────────────────────────────────────────────────────
access_lines = []

for p in people:
    pid   = p.get(per_nt['id_col'], '').strip()
    email = p['email_primary'].strip()
    if not pid:
        continue
    sec_cfg = (config['security'] or {}).get(email, {}) or {}
    label  = str(sec_cfg.get('label',  '') or p['security_label'].strip()  or 'Internal')
    policy = str(sec_cfg.get('policy', '') or p['access_policy'].strip()   or 'policy-consortium-read')
    tenant = p['tenant'].strip() or 'consortium-alpha'
    access_lines.append(
        f"person:{pid} ex:securityLabel {lit(label)} ; ex:accessPolicy {lit(policy)} ; ex:tenant {lit(tenant)} ."
    )

for row in pubs:
    pub_id = row.get(pub_nt['id_col'], '').strip()
    if not pub_id:
        continue
    label  = row['security_label'].strip() or 'Public'
    policy = row['access_policy'].strip()  or 'policy-public-read'
    tenant = row['tenant'].strip()         or 'consortium-alpha'
    access_lines.append(
        f"pub:{pub_id} ex:securityLabel {lit(label)} ; ex:accessPolicy {lit(policy)} ; ex:tenant {lit(tenant)} ."
    )

# ─────────────────────────────────────────────────────────────────────────────
# graph:provenance
# ─────────────────────────────────────────────────────────────────────────────
prov_lines = []

for row in pubs:
    pub_id = row.get(pub_nt['id_col'], '').strip()
    if not pub_id:
        continue
    agent = row['ingestion_agent'].strip()
    if agent:
        prov_lines.append(
            f"pub:{pub_id} prov:wasAttributedTo [ a prov:Agent ; schema:name {lit(agent)} ] ."
        )

# ─────────────────────────────────────────────────────────────────────────────
# Assemble TriG
# ─────────────────────────────────────────────────────────────────────────────
now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

trig = PREFIXES
trig += f"# Generated: {now}\n"
trig += f"# Source: people.csv ({len(people)} rows) + publications.csv ({len(pubs)} rows)\n\n"

trig += "graph:core {\n\n"
trig += "\n".join(core_lines)
trig += "\n}\n\n"

trig += "graph:claims {\n\n"
trig += "\n".join(claims_lines)
trig += "\n}\n\n"

trig += "graph:derived {\n\n"
trig += "\n".join(derived_lines)
trig += "\n}\n\n"

trig += "graph:access {\n\n"
trig += "\n".join(access_lines)
trig += "\n}\n\n"

trig += "graph:provenance {\n\n"
trig += "\n".join(prov_lines)
trig += "\n}\n"

with open('kg.trig', 'w', encoding='utf-8') as f:
    f.write(trig)

print(f"kg.trig written")
print(f"  people: {len(people)}")
print(f"  publications: {len(pubs)}")
print(f"  authorship claims: {len(authorship_claims)}")
print(f"  working groups: {len(wg_seen)}")
print(f"  derived authorship edges: {len(derived_lines)}")
