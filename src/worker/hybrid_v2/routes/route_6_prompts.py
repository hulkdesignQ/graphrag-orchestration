"""Route 6: Concept Search — Synthesis prompt.

Route 6 restores the LazyGraphRAG insight: community summaries provide
thematic structure.  Unlike Route 3 (MAP-REDUCE), there is NO MAP phase.
Community summaries are passed **directly** to synthesis alongside sentence
evidence, eliminating the lossy claim-extraction step and the N extra LLM
calls that produced +41% latency for +1% containment improvement.

The prompt receives three evidence streams:
  1. Community summaries  — thematic structure from graph communities
  2. Section headings     — structural heading context (title + summary)
  3. Sentence evidence    — direct vector search on source sentences

When ROUTE6_COMMUNITY_EXTRACT=1 (default), the community MAP phase
fetches actual source sentences via Community→Entity→MENTIONS→Sentence
graph traversal, aligning with Microsoft's LazyGraphRAG MAP design.

Design rationale documented in:
  ANALYSIS_ROUTE3_LAZYGRAPHRAG_DEVIATION_AND_ROUTE6_PLAN_2026-02-19.md
"""

# ─────────────────────────────────────────────────────────────────
# CONCEPT SYNTHESIS PROMPT
# ─────────────────────────────────────────────────────────────────
# Input variables: {query}, {community_summaries}, {section_headings},
#                  {sentence_evidence}
# Expected output: final synthesized response

CONCEPT_SYNTHESIS_PROMPT = """\
You are a document analysis assistant. Answer the query using the evidence below.

**Query**: {query}

**Thematic Context** (community summaries from knowledge graph):
{community_summaries}

**Document Structure** (section headings found in source documents):
{section_headings}

**Document Evidence** (passages from source documents, labelled [Document > Section Header]):
{sentence_evidence}

**Rules**:
1. Use all three sources. Thematic context helps you organize; document evidence provides facts. Document structure is a reference list of section headings — do NOT treat each heading as a separate finding. Thematic context entries are topic clusters, NOT separate documents — never present a community theme as if it were a distinct document.
2. Include facts from document evidence even if they are not mentioned in thematic context.
3. Use thematic context to frame your answer — group related findings under clear headings.
4. Preserve important terminology from evidence labels (e.g. role names, section titles, legal terms).
5. Keep specific details: names, amounts, dates, conditions, section references.
6. Response length — choose based on query type:
   - R6-VIII: For queries asking for ALL, EVERY, COMPLETE LIST, or ENUMERATE: list EVERY item found across ALL documents without truncation. Completeness is mandatory — do not summarize or drop items.
   - For narrative/summary queries: 3-5 focused paragraphs, prioritizing the most important findings.
   - PRECISION OVER PADDING: When the query qualifies items with criteria such as "explicitly described as X", "specifically named", "required Y" — only include items where the source evidence EXPLICITLY uses that characterisation. Do not broaden the criteria to include tangentially related items. Omitting a marginal item is always better than including one that doesn't strictly match. For entity/party listing queries, include ALL named organisations, companies, associations, and named bodies (e.g. arbitration administrators, industry associations, job site names). Do NOT include individual persons by name (e.g. "John Doe") unless they operate as a named business entity. Do NOT include governmental jurisdictions (e.g. "County of Washburn") unless they are a contractual party.
7. Cross-document comparison (R6-IX) — for queries asking which document has the latest/earliest/largest/smallest value, or which entity appears most/least:
   a. Extract the relevant value explicitly from EACH document represented in the evidence.
   b. List: "[Document name]: [value found]" for every document.
   c. Then state which is largest/latest/most based only on the extracted values.
   d. If no evidence exists for a document, write "[Document name]: no evidence found" — never guess.
8. Do not mention methodology, sources, or how the evidence was retrieved.
9. REFUSE for specific lookups where the exact data point is absent:
   - Question asks about a specific term, clause, or concept by name (e.g. "mold damage", "force majeure") but that exact term does NOT appear anywhere in the document evidence → say: "The requested information was not found in the available documents." Do NOT infer that an unnamed concept falls under a broader or related category.
   - If no evidence at all is available, say: "The requested information was not found in the available documents."
10. DOCUMENT COVERAGE — For queries asking about clauses, provisions, obligations, or features across multiple documents: scan the evidence for EVERY distinct document, then for each document explicitly assess whether it contains relevant content. Include broader variants of the requested category (e.g. warranty disclaimers and limitation-of-liability clauses are forms of liability protection; risk-of-loss allocation is a form of risk management). Never state "no relevant clauses" for a document without first checking all evidence passages from that document.

**Answer**:
"""

# ─────────────────────────────────────────────────────────────────
# COMMUNITY KEY-POINT EXTRACTION PROMPT  (Microsoft-aligned MAP)
# ─────────────────────────────────────────────────────────────────
# Fetches actual source sentences via Community→Entity→MENTIONS→Sentence
# graph traversal, then extracts query-relevant claims from SOURCE TEXT
# (not from abstract community summaries).
# Input:  {query}, {community_source_text}
# Output: JSON array of key points with importance scores.

COMMUNITY_EXTRACT_PROMPT = """\
You are an analyst. Given the user query and source passages from community-grouped documents, extract ALL specific facts, terms, conditions, or data points that could be useful for answering the query — even if only indirectly relevant.

**Query**: {query}

**Source Passages** (grouped by community theme, labelled by document):
{community_source_text}

**Instructions**:
1. Read ALL source passages across ALL communities. Extract specific facts that relate to the query.
2. Each key point must be a concrete, specific fact — not a vague theme description.
3. Preserve exact terminology: names, amounts, dates, legal terms, conditions, section references.
4. Score each point 0-100 for importance to answering the query. Score ≥ 70 for facts that DIRECTLY answer the query. Score 30-69 for facts that are indirectly relevant or provide supporting context. Score < 30 only for completely unrelated facts.
5. If a community has no relevant facts for this query, skip it entirely.
6. Include facts from EVERY document that contains relevant information — do not focus on just one.
7. COMPLETENESS: Extract ALL obligations, requirements, mechanisms, and named items from the source text that fall within the query's scope. Missing a relevant item is worse than including a borderline one. Include items that substantively match the query's category even if the source text uses different wording (e.g., "prepare an inventory" qualifies as record-keeping; "submit reports to the County" qualifies as reporting).
8. FOCUS: Only extract facts that substantively relate to the query's topic. Do not extract general contract terms, boilerplate provisions, or unrelated obligations just because they appear in the source text.
9. SCOPE INTERPRETATION: When the query mentions a category of clauses or provisions (e.g. "insurance / indemnity / hold harmless"), interpret broadly to include: explicit insurance requirements, indemnification and hold harmless provisions, liability limitations and exclusions, warranty disclaimers, risk-of-loss allocation, and damage exclusion clauses. Extract these from EVERY document in the source passages.

Respond with ONLY a JSON object:
{{"points": [
    {{"description": "specific fact or detail from source text", "score": importance_0_to_100, "community": "community title"}},
    ...
]}}
"""
