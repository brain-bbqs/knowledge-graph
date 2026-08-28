#!/usr/bin/env python3
"""Generate kg.trig from people.csv + publications.csv + config.yaml overlay."""

import csv, json, re, sys, os
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

BASE = "https://brain-bbqs.org/"
PREFIXES = """\
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

def esc(s):
    """Escape a string literal for Turtle."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

def slug(s):
    """Turn a string into a safe IRI segment."""
    return re.sub(r'[^A-Za-z0-9_-]', '_', s.strip())

def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

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

# Build email → config entry lookup
cfg_by_email = {}
for email, entry in config['people'].items():
    if email and entry:
        cfg_by_email[email.strip()] = entry

# ── helpers ──────────────────────────────────────────────────────────────────
def lit(val, dtype=None):
    if dtype:
        return f'"{esc(val)}"^^{dtype}'
    return f'"{esc(val)}"'

def orcid_to_person(orcid, orcid_map):
    """Return person IRI if this ORCID is in the people roster."""
    return orcid_map.get(orcid.strip())

# Build ORCID → person_id map
orcid_map = {}
for p in people:
    if p['orcid'].strip():
        orcid_map[p['orcid'].strip()] = p['person_id'].strip()

# ─────────────────────────────────────────────────────────────────────────────
# graph:core  — canonical entities
# ─────────────────────────────────────────────────────────────────────────────
core_lines = []

for p in people:
    pid = p['person_id'].strip()
    if not pid:
        continue
    s = f"person:{pid}"
    triples = [f"  a schema:Person"]
    if p['name'].strip():
        triples.append(f"  ; schema:name {lit(p['name'].strip())}")
    if p['institution_name'].strip():
        institutions = [i.strip() for i in p['institution_name'].split(',') if i.strip()]
        for inst in institutions:
            triples.append(f"  ; schema:affiliation [ a schema:Organization ; schema:name {lit(inst)} ]")
    if p['role'].strip():
        triples.append(f"  ; ex:consortiumRole {lit(p['role'].strip())}")
    if p['profile_url'].strip():
        triples.append(f"  ; schema:url {lit(p['profile_url'].strip())}")
    if p['orcid'].strip():
        triples.append(f"  ; schema:identifier [ schema:propertyID \"ORCID\" ; schema:value {lit(p['orcid'].strip())} ]")
    if p['scholar_id'].strip():
        triples.append(f"  ; schema:identifier [ schema:propertyID \"GoogleScholar\" ; schema:value {lit(p['scholar_id'].strip())} ]")
    if p['reporter_profile_id'].strip():
        triples.append(f"  ; schema:identifier [ schema:propertyID \"NIH_RePORTER\" ; schema:value {lit(p['reporter_profile_id'].strip())} ]")
    if p['working_groups'].strip():
        for wg in p['working_groups'].split(';'):
            wg = wg.strip()
            if wg:
                triples.append(f"  ; ex:memberOf wg:{slug(wg)}")
    if p['email_primary'].strip():
        triples.append(f"  ; schema:email {lit(p['email_primary'].strip())}")
    if p['generated_at'].strip():
        triples.append(f"  ; prov:generatedAtTime {lit(p['generated_at'].strip(), 'xsd:dateTime')}")
    core_lines.append(f"{s}\n" + "\n".join(triples) + " .\n")

for pub in pubs:
    pub_id = pub['publication_id'].strip()
    if not pub_id:
        continue
    s = f"pub:{pub_id}"
    triples = [f"  a schema:ScholarlyArticle"]
    if pub['title'].strip():
        triples.append(f"  ; dct:title {lit(pub['title'].strip())}")
    if pub['journal'].strip():
        triples.append(f"  ; schema:isPartOf [ a schema:Periodical ; schema:name {lit(pub['journal'].strip())} ]")
    if pub['year'].strip():
        triples.append(f"  ; schema:datePublished {lit(pub['year'].strip(), 'xsd:gYear')}")
    if pub['doi'].strip():
        triples.append(f"  ; schema:identifier [ schema:propertyID \"DOI\" ; schema:value {lit(pub['doi'].strip())} ]")
    if pub['pmid'].strip():
        triples.append(f"  ; schema:identifier [ schema:propertyID \"PMID\" ; schema:value {lit(pub['pmid'].strip())} ]")
    if pub['url'].strip():
        triples.append(f"  ; schema:url {lit(pub['url'].strip())}")
    if pub['citations'].strip():
        triples.append(f"  ; ex:citationCount {lit(pub['citations'].strip(), 'xsd:integer')}")
    if pub['rcr'].strip():
        triples.append(f"  ; ex:relativeCitationRatio {lit(pub['rcr'].strip(), 'xsd:decimal')}")
    if pub['keywords'].strip():
        for kw in pub['keywords'].split(';'):
            kw = kw.strip()
            if kw:
                triples.append(f"  ; schema:keywords {lit(kw)}")
    if pub['generated_at'].strip():
        triples.append(f"  ; prov:generatedAtTime {lit(pub['generated_at'].strip(), 'xsd:dateTime')}")
    core_lines.append(f"{s}\n" + "\n".join(triples) + " .\n")

# Working group entities
wg_seen = set()
for p in people:
    for wg in p['working_groups'].split(';'):
        wg = wg.strip()
        if wg and wg not in wg_seen:
            wg_seen.add(wg)
            core_lines.append(f"wg:{slug(wg)}\n  a ex:WorkingGroup ; schema:name {lit(wg)} .\n")

# ─────────────────────────────────────────────────────────────────────────────
# graph:derived — authorship edges (ORCID-matched)
# ─────────────────────────────────────────────────────────────────────────────
derived_lines = []
authorship_claims = []  # feed into graph:claims

# Build pmid → pub lookup for manual authorship
pmid_to_pub = {p['pmid'].strip(): p for p in pubs if p['pmid'].strip()}
email_to_person_id = {p['email_primary'].strip(): p['person_id'].strip()
                      for p in people if p['email_primary'].strip()}

for pub in pubs:
    pub_id = pub['publication_id'].strip()
    if not pub_id or not pub['author_orcids'].strip():
        continue
    orcids = [o.strip() for o in pub['author_orcids'].split(';') if o.strip()]
    for orcid in orcids:
        if orcid in orcid_map:
            person_id = orcid_map[orcid]
            derived_lines.append(
                f"person:{person_id} schema:author pub:{pub_id} ."
            )
            claim_id = f"authorship-{pub_id[:8]}-{slug(orcid)}"
            authorship_claims.append({
                'claim_id': claim_id,
                'person_id': person_id,
                'pub_id': pub_id,
                'orcid': orcid,
                'doi': pub['doi'].strip(),
                'claim_status': pub['claim_status'].strip() or
                    ('Verified' if pub['doi'].strip() else ''),
                'confidence': pub['confidence'].strip(),
                'evidence_source': pub['evidence_source'].strip() or
                    (f"https://doi.org/{pub['doi'].strip()}" if pub['doi'].strip() else pub['url'].strip()),
            })

# Manual authorship links from config.yaml
for entry in config['authorship']:
    pmid    = str(entry.get('pmid', '')).strip()
    email   = str(entry.get('person_email', '')).strip()
    if not pmid or not email:
        continue
    pub_row = pmid_to_pub.get(pmid)
    pid     = email_to_person_id.get(email)
    if not pub_row or not pid:
        print(f"  [config] WARNING: authorship entry not matched — pmid={pmid} email={email}", file=sys.stderr)
        continue
    pub_id   = pub_row['publication_id'].strip()
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
    triples = [f"  a ex:Claim"]
    triples.append(f"  ; ex:subject person:{ac['person_id']}")
    triples.append(f"  ; ex:predicate schema:author")
    triples.append(f"  ; ex:object pub:{ac['pub_id']}")
    if ac['claim_status']:
        triples.append(f"  ; ex:claimStatus {lit(ac['claim_status'])}")
    if ac['confidence']:
        triples.append(f"  ; ex:confidence {lit(ac['confidence'], 'xsd:decimal')}")
    if ac['evidence_source']:
        triples.append(f"  ; ex:hasEvidence [ dct:source <{ac['evidence_source']}> ]")
    claims_lines.append(f"claim:{cid}\n" + "\n".join(triples) + " .\n")

# Identity claims for people (L2 — CSV values merged with config.yaml overlay)
for p in people:
    pid   = p['person_id'].strip()
    email = p['email_primary'].strip()
    if not pid:
        continue
    cid = f"identity-{pid[:8]}"
    # Merge: config.yaml overrides CSV blanks
    cfg = cfg_by_email.get(email, {}) or {}
    claim_status   = str(cfg.get('claim_status', '') or p['claim_status'].strip()).strip()
    confidence_val = str(cfg.get('confidence',   '') or p['confidence'].strip()).strip()
    evidence_src   = p['evidence_source'].strip()
    asserted_in    = p['asserted_in'].strip()
    notes_val      = str(cfg.get('notes', '') or '').strip()

    triples = [f"  a ex:Claim"]
    triples.append(f"  ; ex:subject person:{pid}")
    triples.append(f"  ; ex:predicate schema:name")
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
    pid   = p['person_id'].strip()
    email = p['email_primary'].strip()
    if not pid:
        continue
    # config.yaml security overrides take precedence
    sec_cfg = (config['security'] or {}).get(email, {}) or {}
    label  = str(sec_cfg.get('label', '') or p['security_label'].strip() or 'Internal')
    policy = str(sec_cfg.get('policy','') or p['access_policy'].strip() or 'policy-consortium-read')
    tenant = p['tenant'].strip() or 'consortium-alpha'
    access_lines.append(
        f"person:{pid} ex:securityLabel {lit(label)} ; ex:accessPolicy {lit(policy)} ; ex:tenant {lit(tenant)} ."
    )

for pub in pubs:
    pub_id = pub['publication_id'].strip()
    if not pub_id:
        continue
    label  = pub['security_label'].strip() or 'Public'
    policy = pub['access_policy'].strip() or 'policy-public-read'
    tenant = pub['tenant'].strip() or 'consortium-alpha'
    access_lines.append(
        f"pub:{pub_id} ex:securityLabel {lit(label)} ; ex:accessPolicy {lit(policy)} ; ex:tenant {lit(tenant)} ."
    )

# ─────────────────────────────────────────────────────────────────────────────
# graph:provenance
# ─────────────────────────────────────────────────────────────────────────────
prov_lines = []
for pub in pubs:
    pub_id = pub['publication_id'].strip()
    if not pub_id:
        continue
    agent = pub['ingestion_agent'].strip()
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
