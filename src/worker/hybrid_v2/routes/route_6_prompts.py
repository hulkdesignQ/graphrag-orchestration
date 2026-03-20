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
1. Use all three sources. Thematic context helps you organize; document evidence provides facts. Document structure is a reference list of section headings — do NOT treat each heading as a separate finding. Thematic context entries are topic clusters, NOT separate documents — never present a community theme as if it were a distinct document. CRITICAL: Thematic summaries (labelled "broad context") are for ORGANIZING your answer, not for extracting additional facts. Only cite obligations, clauses, or provisions that appear in the Document Evidence passages or in extracted key points — never introduce new items solely from a thematic summary.
2. Include facts from document evidence even if they are not mentioned in thematic context.
3. Use thematic context to frame your answer — group related findings under clear headings.
4. Preserve important terminology from evidence labels (e.g. role names, section titles, legal terms).
5. Keep specific details: names, amounts, dates, conditions, section references.
6. Response length — choose based on query type:
   - R6-VIII: For queries asking for ALL, EVERY, COMPLETE LIST, or ENUMERATE: list EVERY item found across ALL documents without truncation. Completeness is mandatory — do not summarize or drop items.
   - For narrative/summary queries: 3-5 focused paragraphs, prioritizing the most important findings.
   - PRECISION OVER PADDING: When the query qualifies items with criteria such as "explicitly described as X", "specifically named", "required Y" — only include items where the source evidence EXPLICITLY uses that characterisation. Do not broaden the criteria to include tangentially related items. Omitting a marginal item is always better than including one that doesn't strictly match. In particular: form fields (signatures, registration numbers) are NOT obligations; general contract boilerplate is NOT a specific provision; warranty expiration/termination clauses are NOT "forfeiture terms"; warranty exclusions are NOT "non-refundable terms"; limitation-of-liability clauses are NOT "penalties"; defect-notification procedures ("notify builder in writing") are NOT "record-keeping" — they are notice mechanisms; arbitration confidentiality and arbitration award requirements are NOT "record-keeping" — they are dispute-resolution procedures; invoice fields (customer IDs, PO numbers, dates) are NOT "reporting obligations" — they are transactional identifiers. For entity/party listing queries, include ALL named organisations, companies, associations, and named bodies (e.g. arbitration administrators, industry associations, job site names). Do NOT include individual persons by name (e.g. "John Doe") unless they operate as a named business entity. Do NOT include governmental jurisdictions (e.g. "County of Washburn") unless they are a contractual party.
   - EXTRACTION FIDELITY: The thematic context key points were pre-extracted for relevance to this query. Points with importance ≥ 70 are likely relevant. Process each one and include it if it substantively fits the query’s stated category. Apply the category test rigorously: a warranty-defect notification is a “notice” mechanism, not a “record-keeping” obligation; an insurance documentation requirement is not “financial reporting”; arbitration procedures (confidentiality, written awards, scheduling) are “dispute resolution”, not “record-keeping”; invoice identifiers (customer IDs, PO numbers) are transactional data, not “reporting obligations.” However, interpret each category broadly enough to include all substantively matching provisions — for example, different forms of mandated written communication (written notice, written approval, written consent, agreement in writing) all qualify as “notice / delivery mechanisms.” Similarly, filings, submissions, inspections, inventories, and periodic statements all qualify as “reporting / record-keeping.”
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
9. SCOPE INTERPRETATION: When the query mentions a category of clauses or provisions, interpret the category broadly to include all substantively related provisions, even if the source text uses different terminology. For example: "notice / delivery mechanisms" includes not just formal notices and mailings, but also any requirement for written approval, written consent, or agreement in writing — these are all forms of mandated written communication. Similarly, "reporting / record-keeping" includes filings, submissions, inspections, inventories, and periodic statements. Extract from EVERY document in the source passages.
10. CATEGORY PRECISION: When the query asks for items "explicitly described as X" or uses a narrow legal/financial category (e.g., "non-refundable", "forfeiture", "penalty"), only extract items where the source text EXPLICITLY uses that term or a direct synonym. Warranty expiration upon sale is NOT "forfeiture"; warranty exclusions are NOT "non-refundable terms"; limitation-of-liability clauses are NOT "penalties". Score such loosely re-characterised items < 30.

Respond with ONLY a JSON object:
{{"points": [
    {{"description": "specific fact or detail from source text", "score": importance_0_to_100, "community": "community title"}},
    ...
]}}
"""

# ─────────────────────────────────────────────────────────────────
# SYNTHESIS COMPLETENESS CHECK PROMPT
# ─────────────────────────────────────────────────────────────────
# Two-pass completeness: after synthesis, verify that all high-importance
# key points are represented in the answer. If any are missing, integrate
# them into the answer at the appropriate location.
# Input:  {query}, {key_points}, {answer}
# Output: the final answer (unchanged if complete, or patched with
#         missing items integrated)

SYNTHESIS_COMPLETENESS_CHECK_PROMPT = """\
You are a completeness checker. Identify key points with importance ≥ 85 that are genuinely missing from the answer.

**Query**: {query}

**Key Points** (extracted from source documents):
{key_points}

**Current Answer**:
{answer}

**Instructions**:
1. For each key point with importance ≥ 85, check if its specific fact/detail appears anywhere in the answer.
2. A key point is "represented" if the answer mentions the same fact, even with different wording.
3. PRECISION RULE: Only flag a key point as "missing" if it is a CLEAR, DIRECT answer to the query's stated category. Do NOT add:
   - Borderline items that loosely relate to the category (e.g., warranty limitations are NOT "forfeiture terms"; form fields are NOT "obligations")
   - Items the answer may have deliberately excluded for precision
   - Items from a different category than what the query explicitly asks for
4. If ALL relevant key points with importance ≥ 85 are represented, respond with exactly: ALL_COMPLETE
5. If any clearly relevant key points are missing, write ONLY the missing items as brief bullet points. Do NOT repeat items already in the answer. Do NOT rewrite the existing answer.

**Missing items (or ALL_COMPLETE)**:
"""


# ─────────────────────────────────────────────────────────────────
# MAP-REDUCE SYNTHESIS PROMPTS
# ─────────────────────────────────────────────────────────────────
# MAP phase: per-community focused mini-answer from key points.
# REDUCE phase: merge all mini-answers + sentence evidence into final answer.
# Enabled by ROUTE6_MAP_REDUCE_SYNTHESIS=1 (default ON).

COMMUNITY_MAP_SYNTHESIS_PROMPT = """\
You are a document analysis assistant. Write a focused response for ONE thematic area.

**Query**: {query}

**Theme**: {community_title}

**Key Points** (extracted from source documents for this theme):
{community_key_points}

**Instructions**:
1. Write a response covering ALL key points listed above. Every key point with importance ≥ 70 MUST appear.
2. Preserve specific details: names, amounts, dates, conditions, legal terms, section references.
3. Do not add information beyond what the key points provide.
4. Be comprehensive but concise — a well-structured paragraph or short bullet list.
5. Do not mention methodology or how information was retrieved.

**Response**:
"""

REDUCE_SYNTHESIS_PROMPT = """\
You are a document analysis assistant. Merge thematic responses into a final comprehensive answer.

**Query**: {query}

**Thematic Responses** (each covers a different topic area — include ALL items from ALL responses):
{community_responses}

**Document Structure** (section headings found in source documents):
{section_headings}

**Document Evidence** (additional passages from source documents, labelled [Document > Section Header]):
{sentence_evidence}

**Rules**:
1. Include ALL items from ALL thematic responses. Do NOT drop any item. Each thematic response was independently verified for relevance — trust their content.
2. Use document evidence to add specific details, quotes, or facts not already covered by thematic responses.
3. Organize findings under clear headings grouped by theme.
4. Deduplicate: if the same item appears in multiple responses, include it once with the most detail.
5. Keep specific details: names, amounts, dates, conditions, section references.
6. Response length — choose based on query type:
   - R6-VIII: For queries asking for ALL, EVERY, COMPLETE LIST, or ENUMERATE: list EVERY item found across ALL documents without truncation. Completeness is mandatory — do not summarize or drop items.
   - For narrative/summary queries: 3-5 focused paragraphs, prioritizing the most important findings.
   - PRECISION OVER PADDING: When the query qualifies items with criteria such as "explicitly described as X", "specifically named", "required Y" — only include items where the source evidence EXPLICITLY uses that characterisation. Do not broaden the criteria to include tangentially related items.
   - EXTRACTION FIDELITY: Points with importance ≥ 70 are likely relevant. Apply the category test rigorously but interpret each category broadly enough to include all substantively matching provisions.
7. Cross-document comparison (R6-IX) — for queries asking which document has the latest/earliest/largest/smallest value:
   a. Extract the relevant value explicitly from EACH document.
   b. List: "[Document name]: [value found]" for every document.
   c. Then state which is largest/latest/most based only on the extracted values.
8. Do not mention methodology, sources, or how the evidence was retrieved.
9. REFUSE for specific lookups where the exact data point is absent:
   - If no thematic responses contain relevant information, say: "The requested information was not found in the available documents."
10. DOCUMENT COVERAGE — For queries about clauses, provisions, or features across multiple documents: include findings from EVERY document represented in the thematic responses.

**Answer**:
"""


# ─────────────────────────────────────────────────────────────────
# SELF-CONSISTENCY MERGE PROMPT
# ─────────────────────────────────────────────────────────────────
# Two parallel synthesis calls produce Answer A and Answer B.
# This prompt merges them into a single answer that preserves the
# UNION of all items from both, reducing variance from LLM non-determinism.

SELF_CONSISTENCY_MERGE_PROMPT = """\
You are merging two answers to the same query. Both answers were generated from identical evidence — they differ only due to LLM non-determinism.

**Query**: {query}

**Answer A**:
{answer_a}

**Answer B**:
{answer_b}

**Instructions**:
1. Produce a SINGLE merged answer that includes EVERY distinct item from BOTH answers.
2. If an item appears in only one answer, INCLUDE it — the other answer dropped it by accident.
3. If an item appears in both, include it ONCE with the most detailed version.
4. Do NOT add new information beyond what appears in Answer A or Answer B.
5. PRECISION: If one answer includes an item and the other explicitly states that category has no relevant content, trust the answer that INCLUDES the item (it found something the other missed).
6. However, if one answer includes a borderline item that is NOT a clear match for the query's stated category, OMIT it. For example: warranty coverage expiration is NOT a "non-refundable/forfeiture term"; general boilerplate is NOT a specific provision.
7. Preserve the organizational structure (headings, grouping by document) from whichever answer is better structured.
8. Keep specific details: names, amounts, dates, conditions, section references.
9. Do not mention that this is a merged answer or reference "Answer A" or "Answer B".

**Merged Answer**:
"""
