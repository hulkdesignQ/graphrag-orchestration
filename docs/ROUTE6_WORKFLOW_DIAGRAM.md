
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ROUTE 6: CONCEPT SEARCH WORKFLOW                       │
│                     (Community-Aware Concept Synthesis)                          │
└─────────────────────────────────────────────────────────────────────────────────┘

                                 ┌──────────┐
                                 │  Query   │
                                 └────┬─────┘
                                      │
          ┌───────────────────────────┼────────────────────────────┐
          │                           │                            │
          ▼                           ▼                            ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────────────┐
│ Community Matching   │  │ Sentence Vector     │  │ Section Heading Search   │
│                     │  │ Search              │  │                          │
│ if corpus ≤ 20:     │  │ Neo4j vector index  │  │ Neo4j vector index       │
│   rate ALL comms    │  │ top_k=30            │  │ top_k=10                 │
│ else:               │  │                     │  │                          │
│   embedding top_k=8 │  │                     │  │                          │
└────────┬────────────┘  └────────┬────────────┘  └────────────┬─────────────┘
         │                        │                             │
         ▼                        │                             │
┌─────────────────────┐           │                             │
│ Dynamic Community   │           │                             │
│ Selection (LLM)     │           │                             │
│                     │           │                             │
│ gpt-5.1 rates each  │           │                             │
│ community 0-5       │           │                             │
│ filter < threshold  │           │                             │
└────────┬────────────┘           │                             │
         │                        │                             │
         ▼ (optional)             │                             │
┌─────────────────────┐           │                             │
│ Community Children  │           │                             │
│ Traversal           │           │                             │
│                     │           │                             │
│ Neo4j graph walk    │           │                             │
│ PARENT_COMMUNITY    │           │                             │
└────────┬────────────┘           │                             │
         │                        ▼                             │
         │           ┌──────────────────────────┐               │
         │           │ Step 1b: Entity Expansion │               │
         │           │ (optional)                │               │
         │           │                           │               │
         │           │ Traverse shared entities  │               │
         │           │ for multi-hop reasoning   │               │
         │           └────────────┬──────────────┘               │
         │                        │                             │
         │    ┌───────────────────┘                             │
         │    │                                                 │
         │    ▼                                                 │
         │  ╔══════════════════════════════════════╗            │
         │  ║  STEP 2: DENOISE + RERANK            ║            │
         │  ╠══════════════════════════════════════╣            │
         │  ║                                      ║            │
         │  ║  1. Denoise (remove boilerplate)     ║            │
         │  ║  2. Diversity selection               ║            │
         │  ║     (2× pool, min 2/doc, gate 0.85)  ║            │
         │  ║  3. Inject expanded sentences        ║            │
         │  ║  4. Rerank (Cohere rerank-2.5)       ║            │
         │  ║     → final top_k=15                 ║            │
         │  ║                                      ║            │
         │  ╚════════════════╤═════════════════════╝            │
         │                   │                                  │
         ▼                   ▼                                  ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │                  STEP 3: BUILD SYNTHESIS PROMPT                  │
   ├─────────────────────────────────────────────────────────────────┤
   │                                                                 │
   │  ┌─ Community Extract (MAP phase) ──────────────────────────┐   │
   │  │                                                          │   │
   │  │  For top-12 communities (rating ≥ 1):                    │   │
   │  │    1. Fetch source sentences from Neo4j                  │   │
   │  │    2. Per-community LLM extraction (parallel)            │   │
   │  │       → key points with importance scores                │   │
   │  │    3. Deduplicate (first 60 chars)                       │   │
   │  │    4. Filter (score ≥ 20), cap at 30 points              │   │
   │  │                                                          │   │
   │  │  + Hybrid fallback: append raw summaries for ALL         │   │
   │  │    communities (200 chars) as broad context              │   │
   │  └──────────────────────────────────────────────────────────┘   │
   │                                                                 │
   │  Prompt assembly:                                               │
   │    Part A: Extracted key points + raw summaries                 │
   │    Part B: Section headings (structural context)                │
   │    Part C: Reranked sentence evidence (with citations)          │
   │                                                                 │
   └──────────────────────────────┬──────────────────────────────────┘
                                  │
                                  ▼
                    ╔═══════════════════════════╗
                    ║  SYNTHESIS LLM (gpt-5.1)  ║
                    ║                           ║
                    ║  CONCEPT_SYNTHESIS_PROMPT  ║
                    ║  10 rules including:       ║
                    ║  • Citation requirements   ║
                    ║  • Precision over padding  ║
                    ║  • Document coverage       ║
                    ║  • Scope interpretation    ║
                    ║  • Negative detection      ║
                    ║  temperature=0.0           ║
                    ╚═════════════╤═════════════╝
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │  Post-processing          │
                    │                           │
                    │  • Build citations         │
                    │  • Enrich with geometry    │
                    │  • Assemble metadata       │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                           ┌────────────┐
                           │ RouteResult │
                           │             │
                           │ • response  │
                           │ • citations │
                           │ • evidence  │
                           │ • metadata  │
                           └─────────────┘


═══════════════════════════════════════════════════════════════════
 KEY PARAMETERS                    CURRENT VALUES
═══════════════════════════════════════════════════════════════════
 ROUTE6_COMMUNITY_TOP_K            8
 ROUTE6_RATE_ALL_THRESHOLD         20 (if ≤20 comms, rate all)
 ROUTE6_SENTENCE_TOP_K             30
 ROUTE6_SECTION_TOP_K              10
 ROUTE6_RERANK_TOP_K               15
 ROUTE6_EXTRACT_TOP_K              12
 ROUTE6_EXTRACT_MIN_RATING         1
 ROUTE6_MAX_EXTRACT_POINTS         30
 ROUTE6_EXTRACT_MIN_SCORE          20
 ROUTE6_DYNAMIC_COMMUNITY          1 (enabled)
 ROUTE6_ENTITY_EXPANSION           0 (disabled)
 ROUTE6_COMMUNITY_CHILDREN         0 (disabled)
 ROUTE6_SENTENCE_DIVERSITY         1 (enabled)
 ROUTE6_SENTENCE_RERANK            1 (enabled)
═══════════════════════════════════════════════════════════════════
