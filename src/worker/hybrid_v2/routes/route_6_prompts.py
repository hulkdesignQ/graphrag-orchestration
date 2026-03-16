"""Route 6: Concept Search — Synthesis prompts.

Route 6 follows the Microsoft GraphRAG global search MAP-REDUCE design:
  1. Community MAP extraction — per-community LLM call to extract key points
     from source sentences (Community→Entity→MENTIONS→Sentence traversal).
  2. Per-community MAP synthesis — each community produces a focused
     mini-answer from its key points + sentence evidence.
  3. REDUCE synthesis — merge all mini-answers into the final response.

The MAP-REDUCE synthesis (toggled by ROUTE6_MAP_REDUCE_SYNTHESIS=1) solves
the LLM variance problem: each MAP call sees only 3-5 focused points, so
it cannot "forget" items. The REDUCE step just organises/merges.

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
   - PRECISION OVER PADDING: When the query qualifies items with criteria such as "explicitly described as X", "specifically named", "required Y" — only include items where the source evidence EXPLICITLY uses that characterisation. Do not broaden the criteria to include tangentially related items. Omitting a marginal item is always better than including one that doesn't strictly match. In particular: form fields (signatures, registration numbers) are NOT obligations; general contract boilerplate is NOT a specific provision. For entity/party listing queries, include ALL named organisations, companies, associations, and named bodies (e.g. arbitration administrators, industry associations, job site names). Do NOT include individual persons by name (e.g. "John Doe") unless they operate as a named business entity. Do NOT include governmental jurisdictions (e.g. "County of Washburn") unless they are a contractual party.
   - EXTRACTION FIDELITY: The thematic context key points were pre-extracted for relevance to this query. Points with importance ≥ 70 are likely relevant. Process each one and include it if it substantively fits the query’s stated category. Apply the category test rigorously: a warranty-defect notification is a “notice” mechanism, not a “record-keeping” obligation; an insurance documentation requirement is not “financial reporting.” However, interpret each category broadly enough to include all substantively matching provisions — for example, different forms of mandated written communication (written notice, written approval, written consent, agreement in writing) all qualify as “notice / delivery mechanisms.” Similarly, filings, submissions, inspections, inventories, and periodic statements all qualify as “reporting / record-keeping.”
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

Respond with ONLY a JSON object:
{{"points": [
    {{"description": "specific fact or detail from source text", "score": importance_0_to_100, "community": "community title"}},
    ...
]}}
"""

# ─────────────────────────────────────────────────────────────────
# MAP SYNTHESIS PROMPT  (per-community mini-answer)
# ─────────────────────────────────────────────────────────────────
# Called once per community in parallel.  Each call receives only that
# community's key points and sentence evidence, so the LLM gives focused
# attention to a small set of items — eliminating the variance caused by
# a single monolithic synthesis dropping items from a large context.
#
# Input:  {query}, {community_title}, {key_points}, {sentence_evidence}
# Output: free-text mini-answer (paragraph/bullets) for this community

COMMUNITY_MAP_SYNTHESIS_PROMPT = """\
You are a document analysis assistant. Produce a focused response to the query using ONLY the evidence from this thematic community.

**Query**: {query}

**Community Theme**: {community_title}

**Key Points** (pre-extracted facts relevant to the query):
{key_points}

**Supporting Sentences** (source passages from this community's documents):
{sentence_evidence}

**Rules**:
1. Include EVERY key point that substantively answers the query. Missing an item is the worst possible error.
2. Preserve exact details: names, amounts, dates, conditions, legal terms, section references.
3. Cite the source document for each fact using [Document > Section] notation where available.
4. If no key points or sentences are relevant to the query, respond with exactly: "(No relevant information in this community.)"
5. Keep the response focused and concise — bullet points preferred. Do NOT add introduction or conclusion.
6. Do not mention methodology, the community theme name, or how evidence was obtained.
7. PRECISION: Only include items that substantively match the query's stated category. A warranty limitation-of-liability clause is NOT a "non-refundable / forfeiture" term; a defect notification procedure is NOT a "record-keeping" obligation. If a key point does not fit the query's category, skip it. Do NOT include individual persons by name (e.g. "John Doe") for entity-listing queries unless they operate as a named business.

**Response**:
"""

# ─────────────────────────────────────────────────────────────────
# REDUCE SYNTHESIS PROMPT  (merge community mini-answers)
# ─────────────────────────────────────────────────────────────────
# Receives all MAP mini-answers and produces the final user-facing response.
# The hard work (extracting facts) is done — this step just organises,
# deduplicates, and formats.
#
# Input:  {query}, {community_responses}, {section_headings}
# Output: final synthesized response

REDUCE_SYNTHESIS_PROMPT = """\
You are a document analysis assistant. Combine the analyst reports below into a single, comprehensive answer to the query.

**Query**: {query}

**Analyst Reports** (each report covers a different thematic area of the documents):
{community_responses}

**Document Evidence** (source passages — use these to verify and supplement the analyst reports):
{sentence_evidence}

**Document Structure** (section headings found in source documents):
{section_headings}

**Rules**:
1. Combine ALL analyst reports into one unified answer. Every fact from every report must appear — do NOT drop or summarize away any item.
2. CROSS-CHECK with Document Evidence: scan the source passages for facts NOT covered by any analyst report. If a passage contains a relevant fact that no report mentions, include it in your answer. The analyst reports may have gaps — the document evidence is the ground truth.
3. Deduplicate: if multiple reports or passages mention the same fact, include it once with the most specific detail.
4. Organise by theme or document — group related findings under clear headings.
5. Preserve specific details: names, amounts, dates, conditions, section references, document citations.
6. Response length — choose based on query type:
   - For queries asking for ALL, EVERY, COMPLETE LIST, or ENUMERATE: list EVERY item without truncation. Completeness is mandatory.
   - For narrative/summary queries: 3-5 focused paragraphs.
   - PRECISION OVER PADDING: form fields (signatures, registration numbers) are NOT obligations; general contract boilerplate is NOT a specific provision. Do NOT include individual persons by name unless they operate as a named business. Do NOT include governmental jurisdictions unless they are a contractual party.
7. Cross-document comparison — for queries asking which document has the latest/earliest/largest/smallest value:
   a. List: "[Document name]: [value found]" for every document.
   b. State which is largest/latest/most based only on the extracted values.
8. Do not mention methodology, analyst reports, or how the evidence was retrieved.
9. REFUSE for specific lookups where the exact data point is absent:
   - Question asks about a specific term, clause, or concept by name but that exact term does NOT appear in ANY analyst report or document evidence → say: "The requested information was not found in the available documents."
10. DOCUMENT COVERAGE — For queries about clauses or provisions across documents: ensure EVERY document represented in the analyst reports AND document evidence is covered.

**Answer**:
"""
