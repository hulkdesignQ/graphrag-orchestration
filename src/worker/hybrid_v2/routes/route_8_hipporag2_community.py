"""Route 8: HippoRAG 2 + Community-Seeded PPR (experimental).

Fork of Route 7 with Neural PPR + dynamic reranker cutoff.  Neural PPR
(cosine teleportation) gives every passage query-relevance mass, achieving
100% retrieval recall without community passage seeds or entity injection.
The Voyage reranker's relevance_score drives a dynamic cutoff (threshold
0.25) that replaces fixed top-K and doc interleaving.

Key differences from Route 7 default preset:
  - neural_weight: 0.5          (query-conditioned PPR teleportation)
  - rerank_dynamic_cutoff: True  (score-based passage filtering)
  - community_passage_seeds: OFF (Neural PPR supersedes injection)
  - entity_context_inject: OFF   (PPR already retrieves entity passages)
  - semantic_passage_seeds: OFF  (Neural PPR supersedes cross-encoder seeds)
  - community_guided_instruction: OFF (dynamic cutoff handles filtering)
  - ROUTE_NAME = "route_8_hipporag2_community"
  - Env-var prefix: ROUTE8_* (falls back to ROUTE7_* then defaults)

All other Route 7 features (DPR seeds, triple linking, sentence search,
structural seeds, reranking, synthesis) work identically.

Reference: https://arxiv.org/abs/2502.14802
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import structlog

from src.core.config import settings
from .base import BaseRouteHandler, Citation, RouteResult, acomplete_with_retry, rerank_with_retry, make_voyage_client
from ..services.neo4j_retry import retry_session

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Entity-doc map v2: exhaustive entity enumeration support
# ---------------------------------------------------------------------------
# Maps query-object keywords to the 5 fixed Entity.type values.
# The type schema is set at indexing time and is NOT corpus-specific.
_ENTITY_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "ORGANIZATION": [
        "party", "parties", "organization", "organizations",
        "company", "companies", "firm", "firms",
        "entity", "entities", "contractor", "contractors",
        "vendor", "vendors", "principal", "principals",
        "institution", "institutions", "agency", "agencies",
    ],
    "PERSON": [
        "party", "parties", "people", "individual", "individuals",
        "person", "persons", "signatory", "signatories",
        "representative", "representatives", "personnel",
        "author", "authors", "contributor", "contributors",
    ],
    "LOCATION": [
        "location", "locations", "place", "places",
        "address", "addresses", "jurisdiction", "jurisdictions",
        "city", "cities", "state", "states", "country", "countries",
        "region", "regions", "site", "sites",
    ],
}

# Structural signals for exhaustive intent (no domain nouns)
_EXHAUSTIVE_INTENT_RE = re.compile(
    r"(?:"
    r"\b(?:list|enumerate|identify|name|find|what\s+are|show|extract|gather)\b"
    r".{0,40}"
    r"\b(?:all|every|each|across)\b"
    r"|"
    # Entity comparison: "across the set, which entity appears in the most documents"
    r"\b(?:across)\b.{0,60}\b(?:which|what|compare)\b"
    r")",
    re.IGNORECASE,
)

# Corpus-scope confirmation (query must reference documents/corpus)
_CORPUS_SCOPE_RE = re.compile(
    r"\b(?:documents?|files?|records?|reports?|pages?|corpus|set|collection|data(?:set)?)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Generic role-label filter for entity-doc map.
# Entity extraction often promotes generic role descriptors (e.g. "Builder",
# "Customer", "Agent") to Entity nodes.  These are not named parties and
# should be excluded from the entity-doc map to avoid over-generation.
# Matching is case-insensitive on the normalized (stripped, lowered) name.
# ---------------------------------------------------------------------------
_ROLE_LABEL_BLOCKLIST: set = {
    # generic role labels (not named entities)
    "owner", "agent", "customer", "contractor", "subcontractor",
    "vendor", "supplier", "manufacturer", "administrator",
    "manager", "principal", "representative",
    "authorized representative", "author", "editor",
    # generic relational labels
    "party", "parties", "member", "participant",
    "sender", "receiver", "recipient", "user",
}


def _is_role_label(entity_name: str) -> bool:
    """Return True if the entity name is a generic role label."""
    return entity_name.strip().lower() in _ROLE_LABEL_BLOCKLIST


# Structured relationship types to surface in the entity-doc map Role column.
# These are common graph relationship labels from entity extraction.
_STRUCTURED_ROLE_TYPES: list = [
    "PARTY_TO", "LOCATED_IN", "DEFINES", "REFERENCES", "FOUND_IN",
    "BELONGS_TO", "PART_OF", "HAS", "CONTAINS", "RELATED_TO",
]

# ---------------------------------------------------------------------------
# Voyage embedding service — shared singleton (same pattern as Route 5)
# ---------------------------------------------------------------------------
_voyage_service = None
_voyage_init_attempted = False
_voyage_init_lock = threading.Lock()


def _get_voyage_service():
    """Get Voyage embedding service for query + triple embedding."""
    global _voyage_service, _voyage_init_attempted
    if _voyage_init_attempted:
        return _voyage_service
    with _voyage_init_lock:
        if not _voyage_init_attempted:
            try:
                from src.core.config import settings

                if settings.VOYAGE_API_KEY:
                    from src.worker.hybrid_v2.embeddings.voyage_embed import VoyageEmbedService

                    _voyage_service = VoyageEmbedService()
                    _voyage_init_attempted = True
                    logger.info("route7_voyage_service_initialized")
                else:
                    # Missing API key is a permanent config issue — don't retry
                    _voyage_init_attempted = True
                    logger.warning("route7_voyage_service_no_api_key")
            except Exception as e:
                # Transient failure — allow retry on next call
                logger.warning("route7_voyage_service_init_failed", error=str(e))
    return _voyage_service


class HippoRAG2CommunityHandler(BaseRouteHandler):
    """Route 8: HippoRAG 2 + Community-Seeded PPR (experimental).

    Identical to Route 7 except community passage seeding and community-guided
    instruction are ON by default, enabling cross-document thematic retrieval
    without requiring a specific query_mode preset.
    """

    ROUTE_NAME = "route_8_hipporag2_community"

    # Router-adaptive presets: when the orchestrator passes query_mode, Route 7
    # adjusts parameters to match the query type's needs.  Without query_mode
    # (backward-compatible default), all values come from env vars as before.
    QUERY_MODE_PRESETS: Dict[str, Dict[str, Any]] = {
        "local_search": {              # Factual extraction — fast & concise
            "ppr_passage_top_k": 5,
            "prompt_variant": "v1_concise",
            "max_tokens": 150,
            "sentence_window": False,  # skip ±1 enrichment — keeps table-cell citations precise
        },
        "global_search": {             # Thematic/community-level — needs breadth
            "ppr_passage_top_k": 15,
            "prompt_variant": None,
            "max_tokens": None,
        },
        "drift_multi_hop": {           # Multi-hop reasoning — full context
            "ppr_passage_top_k": 20,
            "prompt_variant": None,
            "max_tokens": None,
        },
        "community_search": {          # Community-dominant (abstract themes, exhaustive)
            "ppr_passage_top_k": 100,  # wider net — dynamic reranker handles filtering
            "prompt_variant": None,
            "max_tokens": None,
            "community_passage_seeds": False,  # Neural PPR achieves 100% recall — injection redundant
            "community_guided_instruction": False,  # dynamic cutoff handles filtering; guided narrows too aggressively (-24% facts)
            "rerank_dynamic_cutoff": True,   # let reranker score decide which passages survive
            "rerank_relevance_threshold": 0.25,  # natural breakpoint — keeps ~25-40 passages per query
            "rerank_top_k": 260,  # wide net — Voyage scores all, threshold filters
            "rerank_prefilter_k": 120,  # cosine pre-filter before cross-encoder reranking
            "min_chunks_per_doc": 0,  # disabled — dynamic cutoff handles passage selection
            "max_chunks_per_doc": 0,  # disabled — dynamic cutoff handles passage selection
            "entity_context_inject": False,  # disabled — PPR already retrieves entity-linked passages
            "semantic_passage_seeds": False,  # disabled — Neural PPR (cosine teleportation) supersedes
            "neural_weight": 0.5,  # query-conditioned teleportation — 100% recall without injection
            "map_reduce_synthesis": True,  # per-document MAP extraction → cross-doc REDUCE merge
            "section_graph": True,  # load Section nodes + SHARES_ENTITY edges in PPR
            # Unified PPR modifiers — available via config_overrides for A/B testing:
            #   hub_penalty_mode: "log"           (1/log(B+degree)^alpha hub tax)
            #   hub_penalty_alpha: "1.5"          (exponent — 1.0 mild, 2.0 strong)
            #   hub_penalty_base: "2.0"           (base — lower = sharper differentiation)
            #   symmetric_norm: "all"|"entity_only" ("all" or entity↔entity only)
            #   community_balanced_seeds: "1"     (boost sparse communities)
            #   community_balance_alpha: "0.3"    (0=log formula, >0=power-law 1/size^alpha)
        },
    }

    def __init__(self, pipeline: Any) -> None:
        super().__init__(pipeline)
        self._triple_store = None
        self._ppr_engine = None
        self._init_lock = asyncio.Lock()

    async def _ensure_initialized(self) -> None:
        """Lazy-load triple embeddings and PPR graph on first query."""
        if self._triple_store is not None and self._ppr_engine is not None:
            return

        async with self._init_lock:
            # Double-check after acquiring lock
            if self._triple_store is not None and self._ppr_engine is not None:
                return

            from ..retrievers.triple_store import TripleEmbeddingStore
            from ..retrievers.hipporag2_ppr import HippoRAG2PPR

            voyage_service = _get_voyage_service()
            if not voyage_service:
                raise RuntimeError("Voyage API key required for Route 7")

            include_section_graph = os.getenv(
                "ROUTE7_SECTION_GRAPH", "1"
            ).strip().lower() in {"1", "true", "yes"}

            passage_node_weight = float(
                os.getenv("ROUTE7_PASSAGE_NODE_WEIGHT", "0.05")
            )
            synonym_threshold = float(
                os.getenv("ROUTE7_SYNONYM_THRESHOLD", "0.70")
            )
            section_edge_weight = float(
                os.getenv("ROUTE7_SECTION_EDGE_WEIGHT", "0.1")
            )
            section_sim_threshold = float(
                os.getenv("ROUTE7_SECTION_SIM_THRESHOLD", "0.5")
            )
            include_appears_in_section = os.getenv(
                "ROUTE7_APPEARS_IN_SECTION", "0"
            ).strip().lower() in {"1", "true", "yes"}
            include_next_in_section = os.getenv(
                "ROUTE7_NEXT_IN_SECTION", "0"
            ).strip().lower() in {"1", "true", "yes"}

            # Load triple store and PPR graph in parallel
            triple_store = TripleEmbeddingStore()
            ppr_engine = HippoRAG2PPR()

            await asyncio.gather(
                triple_store.load(
                    self.neo4j_driver, self.group_id, voyage_service,
                    group_ids=self.group_ids,
                ),
                ppr_engine.load_graph(
                    self.neo4j_driver,
                    self.group_ids,
                    passage_node_weight=passage_node_weight,
                    synonym_threshold=synonym_threshold,
                    include_section_graph=include_section_graph,
                    section_edge_weight=section_edge_weight,
                    section_sim_threshold=section_sim_threshold,
                    include_appears_in_section=include_appears_in_section,
                    include_next_in_section=include_next_in_section,
                ),
            )

            self._triple_store = triple_store
            self._ppr_engine = ppr_engine

            logger.info(
                "route7_initialized",
                triple_count=triple_store.triple_count,
                graph_nodes=ppr_engine.node_count,
            )

    async def execute(
        self,
        query: str,
        response_type: str = "summary",
        knn_config: Optional[str] = None,
        prompt_variant: Optional[str] = None,
        synthesis_model: Optional[str] = None,
        include_context: bool = False,
        weight_profile: Optional[str] = None,
        language: Optional[str] = None,
        query_mode: Optional[str] = None,
        folder_id: Optional[str] = None,
        config_overrides: Optional[Dict[str, str]] = None,
        user_id: Optional[str] = None,
    ) -> RouteResult:
        """Execute Route 7: True HippoRAG 2 retrieval pipeline."""
        # Resolve per-query folder scope (overrides pipeline default)
        folder_id = self._resolve_folder_id(folder_id)

        enable_timings = os.getenv(
            "ROUTE7_RETURN_TIMINGS", "0"
        ).strip().lower() in {"1", "true", "yes"}
        timings_ms: Dict[str, int] = {}
        t_route_start = time.perf_counter()

        # Apply query_mode preset (router-adaptive parameters)
        preset = self.QUERY_MODE_PRESETS.get(query_mode or "", {})
        _co = config_overrides or {}

        # Config from env, with per-request overrides taking precedence.
        # Priority: config_overrides → ROUTE8_env → preset value → ROUTE7_env → default.
        # When the preset explicitly defines a key, ROUTE7_ env vars from .env
        # do NOT override it (prevents route-7 defaults from clobbering the
        # community_search preset).  Use ROUTE8_ env vars to override preset.
        def _ov(key: str, env_var: str, default: str) -> str:
            val = _co.get(key)
            if val:
                return val
            if env_var.startswith("ROUTE7_"):
                r8_val = os.getenv("ROUTE8_" + env_var[7:])
                if r8_val is not None:
                    return r8_val
            if key in preset:
                return default
            return os.getenv(env_var, default)

        triple_top_k = int(_ov("triple_top_k", "ROUTE7_TRIPLE_TOP_K", "15"))
        dpr_top_k = int(_ov("dpr_top_k", "ROUTE7_DPR_TOP_K", "50"))  # upstream default; set -1 to disable
        dpr_sentence_top_k = int(_ov("dpr_sentence_top_k", "ROUTE7_DPR_SENTENCE_TOP_K", "0"))
        ppr_damping = float(_ov("damping", "ROUTE7_DAMPING", "0.5"))
        passage_node_weight = float(_ov("passage_node_weight", "ROUTE7_PASSAGE_NODE_WEIGHT", "0.05"))
        ppr_passage_top_k = int(_ov(
            "ppr_passage_top_k", "ROUTE7_PPR_PASSAGE_TOP_K",
            str(preset.get("ppr_passage_top_k", 50))
        ))
        # Reranker: enabled by default — cross-encoder on PPR output improves Q-D10 accuracy
        rerank_enabled = _ov("rerank", "ROUTE7_RERANK", "1").strip().lower() in {"1", "true", "yes"}
        rerank_top_k = int(_ov(
            "rerank_top_k", "ROUTE7_RERANK_TOP_K",
            str(preset.get("rerank_top_k", 30))
        ))
        # Corpus-wide reranker: cross-encoder on ALL passages as parallel retrieval channel
        rerank_all_enabled = _ov("rerank_all", "ROUTE7_RERANK_ALL", "0").strip().lower() in {"1", "true", "yes"}
        rerank_all_top_k = int(_ov("rerank_all_top_k", "ROUTE7_RERANK_ALL_TOP_K", "50"))

        # Preset can override prompt_variant (only if caller didn't explicitly set one)
        if prompt_variant is None and preset.get("prompt_variant"):
            prompt_variant = preset["prompt_variant"]
        # Env var default for hipporag2_search (when no preset/caller override)
        if prompt_variant is None:
            prompt_variant = os.getenv("ROUTE7_PROMPT_VARIANT", "v10_comprehensive") or None

        # Synthesis max_tokens cap (only local_search preset sets this)
        synthesis_max_tokens: Optional[int] = preset.get("max_tokens")

        # Phase 2 feature flags
        structural_seeds_enabled = _ov(
            "structural_seeds", "ROUTE7_STRUCTURAL_SEEDS", "0"
        ).strip().lower() in {"1", "true", "yes"}
        community_seeds_enabled = _ov(
            "community_seeds", "ROUTE7_COMMUNITY_SEEDS", "0"
        ).strip().lower() in {"1", "true", "yes"}
        sentence_search_enabled = _ov(
            "sentence_search", "ROUTE7_SENTENCE_SEARCH", "0"
        ).strip().lower() in {"1", "true", "yes"}

        # Community passage seeding: Community→Entity→Sentence IDs injected
        # into passage_seeds for PPR.  Activated by community_search preset
        # or env var.  Gives community-dominant queries thematic coverage.
        community_passage_seeds_enabled = _ov(
            "community_passage_seeds", "ROUTE8_COMMUNITY_PASSAGE_SEEDS",
            "1" if preset.get("community_passage_seeds", True) else "0"
        ).strip().lower() in {"1", "true", "yes"}
        community_sentence_weight = float(
            _ov("community_sentence_weight", "ROUTE7_COMMUNITY_SENTENCE_WEIGHT", "0.03")
        )

        # Adaptive community selection: instead of a hard top-k, include all
        # communities scoring >= ratio × best_score, up to max_k.
        community_adaptive_ratio = float(
            _ov("community_adaptive_ratio", "ROUTE7_COMMUNITY_ADAPTIVE_RATIO", "0.85")
        )
        community_max_k = int(
            _ov("community_max_k", "ROUTE7_COMMUNITY_MAX_K", "10")
        )

        # Community-guided instruction: use community summaries to steer
        # embedding and reranker queries for thematic precision.
        community_guided_enabled = _ov(
            "community_guided_instruction", "ROUTE8_COMMUNITY_GUIDED_INSTRUCTION",
            "1" if preset.get("community_guided_instruction", True) else "0"
        ).strip().lower() in {"1", "true", "yes"}

        # Dynamic relevance cutoff: use reranker relevance_score instead
        # of fixed top-K.  Keeps all passages above threshold, drops noise.
        rerank_dynamic_cutoff = _ov(
            "rerank_dynamic_cutoff", "ROUTE7_RERANK_DYNAMIC_CUTOFF",
            "1" if preset.get("rerank_dynamic_cutoff", True) else "0"
        ).strip().lower() in {"1", "true", "yes"}
        rerank_relevance_threshold = float(
            _ov("rerank_relevance_threshold", "ROUTE7_RERANK_RELEVANCE_THRESHOLD",
                str(preset.get("rerank_relevance_threshold", 0.15)))
        )
        rerank_dynamic_max = int(
            _ov("rerank_dynamic_max", "ROUTE7_RERANK_DYNAMIC_MAX", "80")
        )

        # Semantic pre-filter: use embedding cosine similarity to densify
        # PPR candidates before cross-encoder reranking.  Reduces noise and
        # keeps context tight so the LLM enumerates all relevant details.
        semantic_prefilter_enabled = _ov(
            "semantic_prefilter", "ROUTE7_SEMANTIC_PREFILTER", "0"
        ).strip().lower() in {"1", "true", "yes"}
        semantic_prefilter_top_n = int(
            _ov("semantic_prefilter_top_n", "ROUTE7_SEMANTIC_PREFILTER_TOP_N", "30")
        )

        # Cross-encoder passage seeding: rerank ALL passages and feed top results
        # into passage_seeds BEFORE PPR, so the graph walk starts from semantically
        # relevant passages (catches graph-isolated sentences that DPR misses).
        semantic_passage_seeds_enabled = _ov(
            "semantic_passage_seeds", "ROUTE7_SEMANTIC_PASSAGE_SEEDS",
            "1" if preset.get("semantic_passage_seeds", True) else "0"
        ).strip().lower() in {"1", "true", "yes"}
        semantic_seed_top_k = int(_ov("semantic_seed_top_k", "ROUTE7_SEMANTIC_SEED_TOP_K", "20"))
        semantic_seed_weight = float(_ov("semantic_seed_weight", "ROUTE7_SEMANTIC_SEED_WEIGHT", "0.05"))

        # Embedding pre-filter: narrow candidates before cross-encoder reranking.
        # 0 = disabled (rerank all passages). >0 = cosine pre-filter to this many.
        rerank_prefilter_k = int(_ov("rerank_prefilter_k", "ROUTE7_RERANK_PREFILTER_K",
                                     str(preset.get("rerank_prefilter_k", 0))))

        # Neural PPR: query-conditioned teleportation.
        # Blends cosine(query, passage_emb) into PPR personalization vector
        # so every passage gets teleportation mass proportional to query relevance.
        # 0.0 = disabled (structural seeds only). >0 = blend ratio.
        neural_weight = float(_ov("neural_weight", "ROUTE7_NEURAL_WEIGHT",
                                    str(preset.get("neural_weight", 0.0))))

        # Triple reranking config (read early for logging)
        triple_rerank_enabled = _ov(
            "triple_rerank", "ROUTE7_TRIPLE_RERANK", "1"
        ).strip().lower() in {"1", "true", "yes"}
        triple_candidates_k = int(_ov("triple_candidates_k", "ROUTE7_TRIPLE_CANDIDATES_K", "500"))

        # PPR coverage fixes (ref: standard PageRank literature)
        ppr_dangling = _ov(
            "ppr_dangling", "ROUTE7_PPR_DANGLING", "0"
        ).strip().lower() in {"1", "true", "yes"}
        ppr_self_loops = float(_ov("ppr_self_loops", "ROUTE7_PPR_SELF_LOOPS", "0.0"))
        ppr_hub_deval = _ov(
            "ppr_hub_deval", "ROUTE7_PPR_HUB_DEVAL", "0"
        ).strip().lower() in {"1", "true", "yes"}

        # Unified PPR: hub penalty, symmetric norm, community-balanced seeds
        ppr_hub_penalty_mode = _ov(
            "hub_penalty_mode", "ROUTE8_HUB_PENALTY_MODE",
            preset.get("hub_penalty_mode", "none")
        ).strip().lower()
        ppr_hub_penalty_alpha = float(_ov(
            "hub_penalty_alpha", "ROUTE8_HUB_PENALTY_ALPHA",
            str(preset.get("hub_penalty_alpha", 1.0))
        ))
        ppr_hub_penalty_base = float(_ov(
            "hub_penalty_base", "ROUTE8_HUB_PENALTY_BASE",
            str(preset.get("hub_penalty_base", 2.0))
        ))
        ppr_symmetric_norm = _ov(
            "symmetric_norm", "ROUTE8_SYMMETRIC_NORM",
            preset.get("symmetric_norm", "off")
        ).strip().lower()
        # Backward compat: "1"/"true" → "all", "0"/"false" → "off"
        if ppr_symmetric_norm in ("1", "true", "yes"):
            ppr_symmetric_norm = "all"
        elif ppr_symmetric_norm in ("0", "false", "no"):
            ppr_symmetric_norm = "off"
        ppr_community_balance = _ov(
            "community_balanced_seeds", "ROUTE8_COMMUNITY_BALANCED_SEEDS",
            "1" if preset.get("community_balanced_seeds", False) else "0"
        ).strip().lower() in {"1", "true", "yes"}
        ppr_community_balance_alpha = float(_ov(
            "community_balance_alpha", "ROUTE8_COMMUNITY_BALANCE_ALPHA",
            str(preset.get("community_balance_alpha", 0.0))
        ))

        # Sentence window: preset provides the default; config_overrides / env
        # can still override (e.g. re-enable windowing for local_search).
        sentence_window_enabled = _ov(
            "sentence_window", "ROUTE7_SENTENCE_WINDOW",
            "1" if preset.get("sentence_window", True) else "0"
        ).strip().lower() in {"1", "true", "yes"}

        # Map-reduce synthesis: per-document extraction → merge.
        # Each document's chunks get their own LLM extraction call so no
        # single dominant document can drown out others.  The merge step
        # deduplicates and formats.  Essential for cross-doc enumeration
        # queries like Q-D3 where warranty docs dominate context.
        map_reduce_synthesis = _ov(
            "map_reduce_synthesis", "ROUTE8_MAP_REDUCE_SYNTHESIS",
            "1" if preset.get("map_reduce_synthesis", False) else "0"
        ).strip().lower() in {"1", "true", "yes"}
        map_reduce_concurrency = int(_ov(
            "map_reduce_concurrency", "ROUTE8_MAP_REDUCE_CONCURRENCY", "8"
        ))

        # Minimum chunks per document guarantee.
        # For global cross-doc questions, PPR may under-represent documents
        # whose entities are structurally peripheral.  This ensures every
        # document in the group gets at least N chunks in synthesis context.
        min_chunks_per_doc = int(_ov(
            "min_chunks_per_doc", "ROUTE8_MIN_CHUNKS_PER_DOC",
            str(preset.get("min_chunks_per_doc", 0))
        ))

        logger.info(
            "route_7_hipporag2_start",
            query=query[:80],
            response_type=response_type,
            damping=ppr_damping,
            triple_top_k=triple_top_k,
            dpr_top_k=dpr_top_k,
            rerank_enabled=rerank_enabled,
            rerank_top_k=rerank_top_k,
            triple_rerank=triple_rerank_enabled,
            triple_candidates_k=triple_candidates_k if triple_rerank_enabled else triple_top_k,
            query_mode=query_mode,
            ppr_passage_top_k=ppr_passage_top_k,
            prompt_variant=prompt_variant,
            sentence_window=sentence_window_enabled,
            config_overrides=bool(_co),
        )

        # ------------------------------------------------------------------
        # Step 0: Initialize (lazy load triple store + PPR graph)
        # ------------------------------------------------------------------
        await self._ensure_initialized()

        # ------------------------------------------------------------------
        # Step 0.5: Early community matching for guided instruction
        #
        # When community_guided_instruction is enabled, fetch the actual
        # sentence texts from matched communities (Community→Entity→Sentence)
        # and use them to guide the reranker.  Concrete sentences give the
        # reranker specific content to match against, unlike abstract summaries.
        # ------------------------------------------------------------------
        community_guided_query = query  # default: unchanged
        if community_guided_enabled and self.pipeline.community_matcher:
            try:
                t0_cg = time.perf_counter()
                _cm = self.pipeline.community_matcher
                _matched_tuples = await _cm.match_communities(
                    query, relative_threshold=community_adaptive_ratio,
                    max_k=community_max_k, folder_id=folder_id,
                )
                if _matched_tuples:
                    community_ids = [
                        c.get("id") for c, _s in _matched_tuples if c.get("id")
                    ]
                    if community_ids and self._async_neo4j:
                        # Fetch top sentence texts from matched communities
                        sent_cypher = """
                        UNWIND $community_ids AS cid
                        MATCH (e:Entity)-[:BELONGS_TO]->(c:Community {id: cid})
                        WHERE c.group_id IN $group_ids AND e.group_id IN $group_ids
                        MATCH (e)<-[:MENTIONS]-(s:Sentence)
                        WHERE s.group_id IN $group_ids
                        OPTIONAL MATCH (s)-[:IN_DOCUMENT]->(d:Document)
                        WHERE d.group_id IN $group_ids
                        RETURN DISTINCT s.text AS text, s.sent_index AS idx
                        ORDER BY idx
                        LIMIT 20
                        """
                        async with self._async_neo4j._get_session() as session:
                            sent_result = await session.run(
                                sent_cypher,
                                community_ids=community_ids,
                                group_ids=self.group_ids,
                                folder_id=folder_id,
                            )
                            sent_records = await sent_result.data()
                        sent_texts = [
                            r["text"][:150] for r in sent_records
                            if r.get("text")
                        ]
                        if sent_texts:
                            community_instruction = (
                                "Focus on passages covering: "
                                + " | ".join(sent_texts)
                                + " "
                            )
                            community_guided_query = community_instruction + query
                            logger.info(
                                "step_0.5_community_sentence_instruction",
                                communities=len(community_ids),
                                sentences=len(sent_texts),
                                instruction_len=len(community_instruction),
                                instruction_text=community_instruction[:500],
                                elapsed_ms=int((time.perf_counter() - t0_cg) * 1000),
                            )
            except Exception as e:
                logger.warning("community_guided_instruction_failed", error=str(e))

        # ------------------------------------------------------------------
        # Step 1: Embed query
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        voyage_service = _get_voyage_service()
        query_embedding = await asyncio.to_thread(voyage_service.embed_query, query)
        timings_ms["step_1_embed_ms"] = int((time.perf_counter() - t0) * 1000)

        # ------------------------------------------------------------------
        # Step 2: Parallel — Triple linking + DPR passage search
        #
        # DPR (dense passage retrieval via sentence_embedding cosine)
        # is the original HippoRAG2 passage seeding method.  Seeds feed
        # into PPR which performs graph-based ranking (the final authority).
        # After PPR, the cross-encoder reranker refines the top passages
        # for synthesis quality.
        # ------------------------------------------------------------------
        t0 = time.perf_counter()

        # 2a. Query-to-triple linking + recognition memory filter
        triple_task = asyncio.create_task(
            self._query_to_triple_linking(query, query_embedding, triple_top_k)
        )

        # 2b. DPR passage search (sentence-level Small-to-Big)
        dpr_task = asyncio.create_task(
            self._dpr_passage_search(query_embedding, dpr_top_k, dpr_sentence_top_k, folder_id=folder_id)
        )

        # 2c. Optional sentence search for evidence augmentation (Phase 2)
        sentence_task = None
        if sentence_search_enabled:
            sentence_top_k = int(os.getenv("ROUTE7_SENTENCE_TOP_K", "30"))
            sentence_task = asyncio.create_task(
                self._retrieve_sentence_evidence(query, top_k=sentence_top_k, folder_id=folder_id)
            )

        # 2d. Optional cross-encoder passage seeding (Priority 2A)
        semantic_seed_task = None
        if semantic_passage_seeds_enabled:
            semantic_seed_task = asyncio.create_task(
                self._rerank_all_passages(
                    query, top_k=semantic_seed_top_k,
                    relevance_threshold=rerank_relevance_threshold if rerank_dynamic_cutoff else 0.0,
                    dynamic_max=rerank_dynamic_max if rerank_dynamic_cutoff else 0,
                    user_id=user_id,
                    prefilter_top_k=rerank_prefilter_k,
                )
            )

        # Await parallel tasks
        tasks = [triple_task, dpr_task]
        if sentence_task:
            tasks.append(sentence_task)
        if semantic_seed_task:
            tasks.append(semantic_seed_task)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Unpack results (positions depend on which optional tasks were added)
        surviving_triples = results[0] if not isinstance(results[0], BaseException) else []
        dpr_results = results[1] if not isinstance(results[1], BaseException) else []

        _idx = 2
        sentence_evidence: List[Dict[str, Any]] = []
        if sentence_task:
            raw_sent = results[_idx] if len(results) > _idx else []
            sentence_evidence = raw_sent if not isinstance(raw_sent, BaseException) else []
            _idx += 1

        semantic_seed_results: List[Tuple[str, float]] = []
        if semantic_seed_task:
            raw_ss = results[_idx] if len(results) > _idx else []
            semantic_seed_results = raw_ss if not isinstance(raw_ss, BaseException) else []

        if isinstance(results[0], BaseException):
            logger.warning("route7_triple_linking_failed", error=str(results[0]))
        if isinstance(results[1], BaseException):
            logger.warning("route7_dpr_failed", error=str(results[1]))

        timings_ms["step_2_parallel_ms"] = int((time.perf_counter() - t0) * 1000)

        logger.info(
            "step_2_parallel_complete",
            surviving_triples=len(surviving_triples),
            dpr_hits=len(dpr_results),
            sentence_hits=len(sentence_evidence),
            semantic_seed_hits=len(semantic_seed_results),
        )

        # ------------------------------------------------------------------
        # Step 3: Build entity seeds from surviving triples
        #   When IDF enabled: min-max normalize fact scores, IDF-weight
        #   by entity document frequency, mean-normalize per entity.
        #   Default OFF — IDF hurts exhaustive queries (e.g. Q-D3) at
        #   small corpus scale by demoting high-frequency seed entities.
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        entity_seeds: Dict[str, float] = {}
        idf_enabled = os.getenv(
            "ROUTE7_IDF_ENABLED", "1"
        ).strip().lower() in {"1", "true", "yes"}

        if idf_enabled:
            # 3a. Min-max normalize fact scores to [0,1] (upstream Deviation 3)
            if surviving_triples:
                _fact_scores = [fs for _, fs in surviving_triples]
                _fs_min, _fs_max = min(_fact_scores), max(_fact_scores)
                _fs_spread = _fs_max - _fs_min if _fs_max > _fs_min else 1.0
            else:
                _fs_min = _fs_spread = 0.0

            # 3b. IDF weighting + accumulation (upstream Deviation 1)
            _entity_mention_counts = (
                self._ppr_engine.entity_mention_counts if self._ppr_engine else {}
            )
            _entity_fact_count: Dict[str, int] = {}
            for triple, raw_fact_score in surviving_triples:
                norm_fact_score = (raw_fact_score - _fs_min) / _fs_spread if _fs_spread else 1.0
                for eid in (triple.subject_id, triple.object_id):
                    doc_freq = max(_entity_mention_counts.get(eid, 1), 1)
                    entity_seeds[eid] = entity_seeds.get(eid, 0) + norm_fact_score / doc_freq
                    _entity_fact_count[eid] = _entity_fact_count.get(eid, 0) + 1

            # 3c. Mean-normalize: average across facts per entity (upstream Deviation 1)
            for eid, n_facts in _entity_fact_count.items():
                if n_facts > 1:
                    entity_seeds[eid] /= n_facts
        else:
            # Original: raw cosine similarity accumulation, no IDF
            for triple, fact_score in surviving_triples:
                for eid in (triple.subject_id, triple.object_id):
                    entity_seeds[eid] = entity_seeds.get(eid, 0) + fact_score

        # Track triple-derived entity IDs — these represent direct query
        # relevance from triple embedding search and should survive the
        # community entity filter (Option A: preserve direct evidence).
        triple_entity_ids: set = set(entity_seeds.keys())

        # Phase 2+3: Add structural seeds (Tier 2) and community seeds (Tier 3) in parallel
        structural_sections: List[str] = []
        community_entity_ids: List[str] = []
        community_data: List[Dict[str, Any]] = []
        community_sentence_ids: List[str] = []
        community_per_community: Dict[str, List[str]] = {}

        _seed_tasks: List[Tuple[str, Any]] = []
        if structural_seeds_enabled and self._async_neo4j:
            _seed_tasks.append(("structural", self._resolve_structural_seeds(query, folder_id=folder_id)))
        # Activate community seeds when either entity seeding OR passage seeding is enabled
        _need_community = (community_seeds_enabled or community_passage_seeds_enabled) and self.pipeline.community_matcher
        if _need_community:
            _seed_tasks.append(("community", self._resolve_community_seeds(
                query, include_sentences=community_passage_seeds_enabled,
                adaptive_ratio=community_adaptive_ratio,
                max_k=community_max_k,
                folder_id=folder_id,
            )))

        if _seed_tasks:
            _seed_results = await asyncio.gather(*[t[1] for t in _seed_tasks])
            for (label, _), result in zip(_seed_tasks, _seed_results):
                if label == "structural":
                    structural_entity_ids, structural_sections = result
                    w_structural = float(os.getenv("ROUTE7_W_STRUCTURAL", "0.2"))
                    for eid in structural_entity_ids:
                        entity_seeds[eid] = entity_seeds.get(eid, 0) + w_structural
                else:
                    community_entity_ids, community_data, community_sentence_ids, community_per_community = result
                    if community_seeds_enabled:
                        w_community = float(os.getenv("ROUTE7_W_COMMUNITY", "0.1"))
                        for eid in community_entity_ids:
                            entity_seeds[eid] = entity_seeds.get(eid, 0) + w_community

        # Community entity filter: when community_passage_seeds is active,
        # restrict entity seeds to those belonging to the matched community.
        # This scopes PPR's walk to the community subgraph, preventing
        # dense clusters from dominating over minority documents.
        #
        # Option A: Triple-derived entity seeds are PRESERVED through the
        # filter — they represent direct query-to-content relevance from
        # triple embedding search and should not be overridden by the
        # indirect community membership signal.  Only community/structural
        # seeds that lack triple backing get filtered.
        if community_passage_seeds_enabled and community_entity_ids:
            community_entity_set = set(community_entity_ids)
            pre_filter = len(entity_seeds)
            entity_seeds = {
                eid: score for eid, score in entity_seeds.items()
                if eid in community_entity_set or eid in triple_entity_ids
            }
            triple_preserved = len([
                eid for eid in entity_seeds
                if eid in triple_entity_ids and eid not in community_entity_set
            ])
            logger.info(
                "step_3_community_entity_filter",
                before=pre_filter,
                after=len(entity_seeds),
                community_entities=len(community_entity_set),
                triple_preserved=triple_preserved,
            )

        # P2: Keep only top-5 entity seeds (upstream alignment)
        # Concentrates PPR mass on the most relevant entities.
        entity_top_k = int(os.getenv("ROUTE7_ENTITY_SEED_TOP_K", "15"))
        if len(entity_seeds) > entity_top_k:
            sorted_entities = sorted(entity_seeds.items(), key=lambda x: -x[1])
            entity_seeds = dict(sorted_entities[:entity_top_k])

        # Build passage seeds from DPR (original HippoRAG2 design)
        # P1: min-max normalize DPR scores to [0,1] (upstream alignment)
        passage_seeds: Dict[str, float] = {}
        if dpr_results:
            _scores = [s for _, s in dpr_results]
            _s_min, _s_max = min(_scores), max(_scores)
            _spread = _s_max - _s_min if _s_max > _s_min else 1.0
            for sentence_id, score in dpr_results:
                normalized = (score - _s_min) / _spread
                passage_seeds[sentence_id] = normalized * passage_node_weight

        # Priority 2A: Cross-encoder passage seeds — merge into passage_seeds
        # so PPR walks from semantically relevant passages (catches graph-isolated
        # sentences that cosine DPR misses, e.g. Q-D3 "day-based timeframes").
        semantic_seeds_added = 0
        if semantic_seed_results:
            # Min-max normalize cross-encoder scores to [0,1]
            _ss_scores = [s for _, s in semantic_seed_results]
            _ss_min, _ss_max = min(_ss_scores), max(_ss_scores)
            _ss_spread = _ss_max - _ss_min if _ss_max > _ss_min else 1.0
            for sentence_id, score in semantic_seed_results:
                normalized = (score - _ss_min) / _ss_spread
                weighted = normalized * semantic_seed_weight
                # Take max of DPR seed and semantic seed (don't stack)
                if sentence_id in passage_seeds:
                    passage_seeds[sentence_id] = max(passage_seeds[sentence_id], weighted)
                else:
                    passage_seeds[sentence_id] = weighted
                    semantic_seeds_added += 1
            logger.info(
                "step_3_semantic_seeds_merged",
                semantic_total=len(semantic_seed_results),
                new_seeds=semantic_seeds_added,
                top_score=round(_ss_max, 4),
            )

        # Community passage seeds: inject Community→Entity→Sentence IDs
        # as low-weight passage seeds so PPR walks from community-linked passages.
        community_seeds_added = 0
        if community_passage_seeds_enabled and community_sentence_ids:
            for sent_eid in community_sentence_ids:
                if sent_eid not in passage_seeds:
                    passage_seeds[sent_eid] = community_sentence_weight
                    community_seeds_added += 1
                # Don't overwrite higher-weighted DPR/semantic seeds
            logger.info(
                "step_3_community_passage_seeds",
                community_sentences=len(community_sentence_ids),
                new_seeds=community_seeds_added,
                weight=community_sentence_weight,
            )

        # ------------------------------------------------------------------
        # Step 3e: Entity embedding seeds — embed the query, search the
        # entity vector index, add top-K matched entities as PPR seeds.
        # This finds entities semantically similar to the question's
        # concepts (e.g. "day-based timeframes" → "90 days",
        # "leases of more than 180 days") that triple search may miss.
        # ------------------------------------------------------------------
        entity_emb_seeds_enabled = _ov(
            "entity_embedding_seeds", "ROUTE8_ENTITY_EMBEDDING_SEEDS", "1"
        ).strip().lower() in {"1", "true", "yes"}
        entity_emb_seeds_added = 0
        emb_entity_ids: List[str] = []
        if entity_emb_seeds_enabled and self._async_neo4j:
            try:
                from src.worker.hybrid_v2.embeddings.voyage_embed import get_voyage_embed_service
                _voyage_svc = get_voyage_embed_service()
                entity_emb_top_k = int(_ov(
                    "entity_embedding_top_k", "ROUTE8_ENTITY_EMBEDDING_TOP_K", "10"
                ))
                entity_emb_weight = float(_ov(
                    "entity_embedding_weight", "ROUTE8_ENTITY_EMBEDDING_WEIGHT", "0.3"
                ))
                # Embed query using same model as entity embeddings
                query_embs = await _voyage_svc.aembed_independent_texts([query])
                if query_embs and query_embs[0]:
                    query_emb = query_embs[0]
                    # Use SEARCH with in-index group_id filter (Cypher 25).
                    cypher = """
                    CYPHER 25
                    MATCH (node:Entity)
                    SEARCH node IN (VECTOR INDEX entity_embedding FOR $emb WHERE node.group_id = $group_id LIMIT $top_k)
                    SCORE AS score
                    RETURN node.id AS entity_id, node.name AS entity_name, score
                    ORDER BY score DESC
                    UNION ALL
                    MATCH (node:Entity)
                    SEARCH node IN (VECTOR INDEX entity_embedding FOR $emb WHERE node.group_id = $global_group_id LIMIT $top_k)
                    SCORE AS score
                    RETURN node.id AS entity_id, node.name AS entity_name, score
                    ORDER BY score DESC
                    """
                    async with self._async_neo4j._get_session() as session:
                        result = await session.run(
                            cypher,
                            top_k=entity_emb_top_k,
                            emb=query_emb,
                            group_id=self.group_ids[0] if self.group_ids else "",
                            global_group_id=self.group_ids[-1] if len(self.group_ids) > 1 else "",
                        )
                        emb_records = await result.data()

                    emb_entity_names = []
                    emb_entity_ids: List[str] = []
                    for rec in emb_records:
                        eid = rec.get("entity_id")
                        if eid:
                            emb_entity_ids.append(eid)
                            if eid not in entity_seeds:
                                entity_seeds[eid] = entity_emb_weight
                                entity_emb_seeds_added += 1
                        emb_entity_names.append(rec.get("entity_name", "?"))

                    logger.info(
                        "step_3e_entity_embedding_seeds",
                        top_k=entity_emb_top_k,
                        matched=len(emb_records),
                        new_seeds=entity_emb_seeds_added,
                        weight=entity_emb_weight,
                        entities=emb_entity_names[:10],
                    )
            except Exception as e:
                logger.warning("step_3e_entity_embedding_seeds_failed", error=str(e))

        # ------------------------------------------------------------------
        # Step 3f: Entity seed expansion — expand entity seeds 1-hop via
        # SEMANTICALLY_SIMILAR edges to bridge semantic gaps.
        # E.g. "dispute" → "claim for loss or injury" (cosine 0.60) brings
        # PMA hold-harmless sentences into PPR reach.
        # ------------------------------------------------------------------
        entity_seed_expansion_enabled = _ov(
            "entity_seed_expansion", "ROUTE8_ENTITY_SEED_EXPANSION", "0"
        ).strip().lower() in {"1", "true", "yes"}
        expansion_min_sim = float(_ov(
            "entity_seed_expansion_min_sim", "ROUTE8_ENTITY_SEED_EXPANSION_MIN_SIM", "0.60"
        ))
        expansion_max_per_seed = int(_ov(
            "entity_seed_expansion_max_per_seed", "ROUTE8_ENTITY_SEED_EXPANSION_MAX_PER_SEED", "3"
        ))
        expansion_base_weight = float(_ov(
            "entity_seed_expansion_weight", "ROUTE8_ENTITY_SEED_EXPANSION_WEIGHT", "0.10"
        ))
        expansion_seeds_added = 0

        if entity_seed_expansion_enabled and entity_seeds and self._async_neo4j:
            try:
                seed_ids = list(entity_seeds.keys())
                async with self._async_neo4j._get_session() as session:
                    # Per-seed top-N expansion: for each seed, take its N
                    # most-similar unseen neighbors. This avoids flooding PPR
                    # with 100+ low-relevance expansions.
                    result = await session.run(
                        """
                        UNWIND $seed_ids AS sid
                        MATCH (e1:Entity {id: sid})-[r:SEMANTICALLY_SIMILAR]-(e2:Entity)
                        WHERE e2.group_id IN $group_ids
                        AND r.similarity >= $min_sim
                        AND NOT e2.id IN $seed_ids
                        WITH sid, e2, r.similarity AS sim
                        ORDER BY sim DESC
                        WITH sid, collect({eid: e2.id, name: e2.name, sim: sim})[0..$max_per_seed] AS top_neighbors
                        UNWIND top_neighbors AS nb
                        RETURN DISTINCT nb.eid AS eid, nb.name AS name,
                               max(nb.sim) AS best_sim
                        ORDER BY best_sim DESC
                        """,
                        seed_ids=seed_ids,
                        group_ids=self.group_ids,
                        min_sim=expansion_min_sim,
                        max_per_seed=expansion_max_per_seed,
                    )
                    expansion_records = await result.data()

                expansion_names = []
                for rec in expansion_records:
                    eid = rec["eid"]
                    if eid not in entity_seeds:
                        # Similarity-proportional weight
                        weight = expansion_base_weight * rec["best_sim"]
                        entity_seeds[eid] = weight
                        expansion_seeds_added += 1
                        expansion_names.append(f"{rec['name']}({rec['best_sim']:.2f})")

                logger.info(
                    "step_3f_entity_seed_expansion",
                    min_sim=expansion_min_sim,
                    max_per_seed=expansion_max_per_seed,
                    candidates=len(expansion_records),
                    new_seeds=expansion_seeds_added,
                    weight_base=expansion_base_weight,
                    entities=expansion_names[:15],
                )
            except Exception as e:
                logger.warning("step_3f_entity_seed_expansion_failed", error=str(e))

        timings_ms["step_3_seed_build_ms"] = int((time.perf_counter() - t0) * 1000)

        logger.info(
            "step_3_seeds_built",
            entity_seeds=len(entity_seeds),
            passage_seeds=len(passage_seeds),
            semantic_seeds_added=semantic_seeds_added,
            community_seeds_added=community_seeds_added,
            entity_emb_seeds_added=entity_emb_seeds_added,
            expansion_seeds_added=expansion_seeds_added,
            entity_seed_names=[k for k in list(entity_seeds.keys())[:15]],
        )

        # ------------------------------------------------------------------
        # Step 4: PPR or DPR-only fallback
        # ------------------------------------------------------------------
        t0 = time.perf_counter()

        if not entity_seeds and not passage_seeds:
            # No seeds at all — return negative result
            return self._empty_result("no_seeds_resolved")

        if not entity_seeds:
            # Bug 13 fix: passage seeds alone can drive PPR via MENTIONS edges
            logger.info("route7_passage_only_ppr", passage_seeds=len(passage_seeds))

        # Always run PPR (entity-only, passage-only, or combined)
        passage_scores, entity_scores = self._ppr_engine.run_ppr(
            entity_seeds=entity_seeds,
            passage_seeds=passage_seeds,
            damping=ppr_damping,
            dangling_redistribution=ppr_dangling,
            passage_self_loops=ppr_self_loops,
            hub_devaluation=ppr_hub_deval,
            hub_penalty_mode=ppr_hub_penalty_mode,
            hub_penalty_alpha=ppr_hub_penalty_alpha,
            hub_penalty_base=ppr_hub_penalty_base,
            symmetric_norm=ppr_symmetric_norm,
            community_balance=ppr_community_balance,
            community_balance_alpha=ppr_community_balance_alpha,
            neural_teleportation=query_embedding if neural_weight > 0 else None,
            neural_weight=neural_weight,
        )

        # Bug 3 fix: if PPR produced no passage scores, fall back to raw DPR order
        if not passage_scores:
            logger.info("route7_dpr_fallback", reason="ppr_no_passage_scores")
            passage_scores = list(dpr_results)
            entity_scores = []

        timings_ms["step_4_ppr_ms"] = int((time.perf_counter() - t0) * 1000)

        # Capture raw PPR output before reranker overwrites passage_scores
        raw_ppr_passage_scores = list(passage_scores)

        logger.info(
            "step_4_ppr_complete",
            top_passages=len(passage_scores[:ppr_passage_top_k]),
            top_entities=len(entity_scores[:20]),
            total_ppr_passages=len(passage_scores),
        )

        # ------------------------------------------------------------------
        # Step 4.5: Rerank PPR output with cross-encoder (optional)
        #
        # The cross-encoder (voyage-rerank-2.5) sees query+passage together
        # and can interpret conceptual matches that cosine similarity misses
        # (e.g., 'time windows' → '3 business days cancellation').
        # This refines PPR's graph-based ranking for synthesis quality
        # while preserving PPR's cross-document diversity.
        # ------------------------------------------------------------------
        graph_structural_header: Optional[str] = None
        entity_doc_rows: List[Dict[str, Any]] = []
        detected_types: Optional[List[str]] = None

        entity_doc_map_enabled = os.getenv(
            "ROUTE7_ENTITY_DOC_MAP", "1"
        ).strip().lower() in {"1", "true", "yes"}

        if rerank_enabled and passage_scores:
            t0_rerank = time.perf_counter()
            # Take PPR's top passages as the candidate pool
            candidate_ids = [cid for cid, _ in passage_scores[:ppr_passage_top_k]]

            # Route 8 addition: inject community-sourced sentence IDs directly
            # into the reranker candidate pool.  PPR seeds give these sentences
            # non-zero probability, but it's usually too low to survive top-K.
            # By adding them as reranker candidates we let the cross-encoder
            # judge relevance independently of graph structure.
            if community_passage_seeds_enabled and community_sentence_ids:
                candidate_set = set(candidate_ids)
                community_direct_injected = 0
                for sent_eid in community_sentence_ids:
                    if sent_eid not in candidate_set:
                        candidate_ids.append(sent_eid)
                        candidate_set.add(sent_eid)
                        community_direct_injected += 1
                if community_direct_injected:
                    logger.info(
                        "step_4.3_community_direct_inject",
                        ppr_candidates=len(candidate_ids) - community_direct_injected,
                        community_injected=community_direct_injected,
                        total_candidates=len(candidate_ids),
                    )

            # Step 4.4: Semantic pre-filter — densify candidates via embedding similarity
            if semantic_prefilter_enabled and len(candidate_ids) > semantic_prefilter_top_n:
                t0_pf = time.perf_counter()
                try:
                    filtered_ids = await self._semantic_prefilter_passages(
                        community_guided_query, candidate_ids, top_n=semantic_prefilter_top_n,
                    )
                    if filtered_ids:
                        logger.info(
                            "step_4.4_semantic_prefilter_complete",
                            input=len(candidate_ids),
                            output=len(filtered_ids),
                            elapsed_ms=int((time.perf_counter() - t0_pf) * 1000),
                        )
                        candidate_ids = filtered_ids
                except Exception as e:
                    logger.warning("step_4.4_prefilter_failed_fallback", error=str(e))

            if len(candidate_ids) >= 2:
                try:
                    reranked_scored = await self._rerank_passages(
                        community_guided_query, candidate_ids, top_k=rerank_top_k,
                        relevance_threshold=rerank_relevance_threshold if rerank_dynamic_cutoff else 0.0,
                        dynamic_max=rerank_dynamic_max if rerank_dynamic_cutoff else 0,
                        user_id=user_id,
                    )
                    if reranked_scored:
                        passage_scores = reranked_scored
                        logger.info(
                            "step_4.5_rerank_ppr_output",
                            candidates=len(candidate_ids),
                            output=len(reranked_scored),
                            dynamic=rerank_dynamic_cutoff,
                            elapsed_ms=int((time.perf_counter() - t0_rerank) * 1000),
                        )
                except Exception as e:
                    logger.warning("step_4.5_rerank_failed_fallback", error=str(e))

            timings_ms["step_4.5_rerank_ms"] = int(
                (time.perf_counter() - t0_rerank) * 1000
            )

        # Step 4.55: Community diversity guarantee
        # After reranking, the reranker output may be dominated by one community
        # (e.g., warranty docs). Ensure every matched community has at least
        # min_per_community sentences in the output. Build a mapping of
        # reranker scores for community sentences, then inject the
        # top-scored sentence from under-represented communities.
        diversity_min = int(_ov("community_diversity_min", "ROUTE8_COMMUNITY_DIVERSITY_MIN", "3"))
        if community_per_community and passage_scores and diversity_min > 0:
            # Map each sentence in reranker output to its communities
            reranked_ids = {cid for cid, _ in passage_scores}
            # Build reranker score lookup for ALL candidates (not just the kept ones)
            # The _rerank_passages call only returns kept items; we need scores for
            # community sentences that may have been dropped. Use step 4.3's
            # injection pool: community_sentence_ids are ALL community sentences.
            community_in_output: Dict[str, int] = {}
            for cid, sids in community_per_community.items():
                in_count = sum(1 for sid in sids if sid in reranked_ids)
                community_in_output[cid] = in_count

            logger.info(
                "step_4.55_community_representation",
                diversity_min=diversity_min,
                communities=len(community_per_community),
                representation=community_in_output,
                reranked_total=len(reranked_ids),
            )

            diversity_injected = 0
            for cid, sids in community_per_community.items():
                if community_in_output.get(cid, 0) >= diversity_min:
                    continue
                # Find this community's sentences that are NOT in the output
                need = diversity_min - community_in_output.get(cid, 0)
                # Prefer sentences that were in the candidate pool (they went
                # through the reranker). The round-robin interleave means earlier
                # positions in the per-community list are more representative.
                for sid in sids[:need * 3]:
                    if sid not in reranked_ids and need > 0:
                        passage_scores.append((sid, 0.01))  # low score, won't displace top items
                        reranked_ids.add(sid)
                        diversity_injected += 1
                        need -= 1
                    if need <= 0:
                        break

            if diversity_injected:
                logger.info(
                    "step_4.55_community_diversity_boost",
                    injected=diversity_injected,
                    communities_boosted={
                        cid: community_in_output.get(cid, 0)
                        for cid in community_per_community
                        if community_in_output.get(cid, 0) < diversity_min
                    },
                    total_passages=len(passage_scores),
                )

        # Step 4.6: Corpus-wide cross-encoder reranking (parallel retrieval channel)
        # Unlike step 4.5 which only reranks PPR top-K, this reranks ALL passages
        # in the corpus and merges top results into PPR output. This catches
        # passages that PPR missed due to graph structure gaps.
        rerank_all_injected = 0
        if rerank_all_enabled:
            t0_ra = time.perf_counter()
            try:
                rerank_all_results = await self._rerank_all_passages(
                    community_guided_query, top_k=rerank_all_top_k,
                    relevance_threshold=rerank_relevance_threshold if rerank_dynamic_cutoff else 0.0,
                    dynamic_max=rerank_dynamic_max if rerank_dynamic_cutoff else 0,
                    user_id=user_id,
                    prefilter_top_k=rerank_prefilter_k,
                )
                if rerank_all_results:
                    # Only dedup against PPR TOP-K (not all PPR passages,
                    # since PPR assigns non-zero scores to every passage)
                    ppr_top_set = {cid for cid, _ in passage_scores[:ppr_passage_top_k]}
                    for cid, score in rerank_all_results:
                        if cid not in ppr_top_set:
                            passage_scores.append((cid, score))
                            rerank_all_injected += 1
                    logger.info(
                        "step_4.6_rerank_all_merge",
                        rerank_all_returned=len(rerank_all_results),
                        injected=rerank_all_injected,
                        already_in_top_k=len(rerank_all_results) - rerank_all_injected,
                    )
            except Exception as e:
                logger.warning("step_4.6_rerank_all_failed", error=str(e))
            timings_ms["step_4.6_rerank_all_ms"] = int(
                (time.perf_counter() - t0_ra) * 1000
            )

        # Determine top passage IDs for chunk fetch.
        # When the reranker used dynamic cutoff, passage_scores may already be
        # shorter than ppr_passage_top_k — respect that instead of inflating
        # back to the original top-K (which would pad with stale PPR tail).
        if rerank_dynamic_cutoff and rerank_enabled and len(passage_scores) < ppr_passage_top_k:
            passage_limit = len(passage_scores) + rerank_all_injected
        else:
            passage_limit = ppr_passage_top_k + rerank_all_injected
        if rerank_all_injected > 0:
            # Re-sort by score so injected passages compete fairly
            passage_scores.sort(key=lambda x: x[1], reverse=True)

        # Step 4.7: LLM relevance filter — reduce over-inclusion for thematic queries
        # Filters the combined passage pool (PPR + rerank-all) through an LLM
        # that decides which passages are truly relevant to the specific question.
        llm_filter_enabled = os.getenv(
            "ROUTE7_LLM_FILTER", "0"
        ).strip().lower() in {"1", "true", "yes"}
        llm_filter_removed = 0
        if llm_filter_enabled and passage_limit > 0:
            t0_filt = time.perf_counter()
            try:
                candidate_passages = passage_scores[:passage_limit]
                text_map = self._ppr_engine.get_all_passage_texts()
                filtered = await self._llm_relevance_filter(
                    query, candidate_passages, text_map,
                )
                if filtered is not None:
                    llm_filter_removed = len(candidate_passages) - len(filtered)
                    # Safety: if filter returned zero passages, the query
                    # likely has no relevant content — keep original set so
                    # synthesis LLM can say "not found" rather than hallucinate.
                    if len(filtered) == 0:
                        logger.info(
                            "step_4.7_llm_filter_skipped_empty",
                            original=len(candidate_passages),
                        )
                    else:
                        passage_scores = filtered + passage_scores[passage_limit:]
                        passage_limit = len(filtered)
                    logger.info(
                        "step_4.7_llm_filter",
                        before=len(candidate_passages),
                        after=len(filtered),
                        removed=llm_filter_removed,
                        applied=len(filtered) > 0,
                    )
            except Exception as e:
                logger.warning("step_4.7_llm_filter_failed", error=str(e))
            timings_ms["step_4.7_llm_filter_ms"] = int(
                (time.perf_counter() - t0_filt) * 1000
            )

        # Step 4.9: Document-interleaved passage selection.
        # The reranker output may be dominated by one or two documents
        # (e.g., warranty docs getting 40 of 55 slots). Interleave
        # top passages from each document in round-robin to guarantee
        # every document with relevant content gets representation.
        # Skip when dynamic cutoff is active — the reranker's threshold
        # already filtered to relevant passages; interleaving would
        # override that decision.
        max_per_doc = int(_ov(
            "max_chunks_per_doc", "ROUTE8_MAX_CHUNKS_PER_DOC",
            str(preset.get("max_chunks_per_doc", 0))
        ))
        if max_per_doc > 0 and passage_scores and not (rerank_dynamic_cutoff and rerank_enabled):
            from collections import defaultdict as _dd, OrderedDict as _OD
            doc_buckets: Dict[str, List[Tuple[str, float]]] = _dd(list)
            for sid, score in passage_scores[:passage_limit]:
                doc_id = sid.split("_sent_")[0] if "_sent_" in sid else "unknown"
                doc_buckets[doc_id].append((sid, score))

            # Round-robin interleave: take 1 from each doc, repeat up to max_per_doc
            interleaved: List[Tuple[str, float]] = []
            doc_counts: Dict[str, int] = {did: 0 for did in doc_buckets}
            for _round in range(max_per_doc):
                for doc_id, items in doc_buckets.items():
                    if doc_counts[doc_id] < len(items) and doc_counts[doc_id] < max_per_doc:
                        interleaved.append(items[doc_counts[doc_id]])
                        doc_counts[doc_id] += 1

            if len(interleaved) != len(passage_scores[:passage_limit]):
                logger.info(
                    "step_4.9_doc_interleave",
                    before=passage_limit,
                    after=len(interleaved),
                    max_per_doc=max_per_doc,
                    doc_counts=doc_counts,
                )
                passage_scores = interleaved + passage_scores[passage_limit:]
                passage_limit = len(interleaved)

        top_passage_scores = passage_scores[:passage_limit]
        top_sentence_ids = [cid for cid, _ in top_passage_scores]
        ppr_scores_map = {cid: score for cid, score in top_passage_scores}

        # Launch parallel tasks: entity-doc map + sentence text fetch
        t0 = time.perf_counter()

        _parallel_tasks: List[Tuple[str, Any]] = []

        # Sentence text fetch (always needed for synthesis)
        _parallel_tasks.append((
            "chunks",
            self._fetch_sentences_by_ids(
                top_sentence_ids,
                ppr_scores_map=ppr_scores_map,
                sentence_window_enabled=sentence_window_enabled,
                folder_id=folder_id,
            ),
        ))

        # Entity-doc map (conditional: only for exhaustive enumeration queries)
        if entity_doc_map_enabled:
            detected_types = self._detect_exhaustive_entity_types(query)
            if detected_types:
                # Always include CONCEPT — many indexing pipelines classify
                # all entities as CONCEPT regardless of semantic type.
                edm_types = list(set(detected_types + ["CONCEPT"]))
                _parallel_tasks.append((
                    "entity_doc_map",
                    self._query_entity_doc_map(edm_types, folder_id=folder_id),
                ))

        _parallel_results = await asyncio.gather(
            *[t[1] for t in _parallel_tasks], return_exceptions=True
        )

        # Unpack chunk fetch result
        pre_fetched_chunks = (
            _parallel_results[0]
            if not isinstance(_parallel_results[0], BaseException)
            else []
        )
        if isinstance(_parallel_results[0], BaseException):
            logger.warning("route7_chunk_fetch_failed", error=str(_parallel_results[0]))

        # DEBUG: dump all fetched chunk texts for PPR output analysis
        if pre_fetched_chunks:
            _debug_texts = []
            for _ch in pre_fetched_chunks:
                _t = _ch.get("text", _ch.get("sentence_text", ""))
                _debug_texts.append(_t[:200])
            logger.info(
                "debug_ppr_fetched_texts",
                num_chunks=len(pre_fetched_chunks),
                texts=_debug_texts,
            )

        # Unpack entity-doc map result (if launched)
        for i, (label, _) in enumerate(_parallel_tasks):
            if label == "entity_doc_map":
                raw_edm = _parallel_results[i]
                if isinstance(raw_edm, BaseException):
                    logger.warning("route7_entity_doc_map_failed", error=str(raw_edm))
                else:
                    entity_doc_rows_raw = raw_edm
                    entity_doc_rows = [
                        r for r in entity_doc_rows_raw
                        if not _is_role_label(r["entity_name"])
                    ]
                    if entity_doc_rows:
                        # Group rows by entity for bullet-list format
                        entity_groups: Dict[
                            Tuple[str, str], List[Dict[str, Any]]
                        ] = defaultdict(list)
                        for row in entity_doc_rows:
                            key = (row["entity_name"], row["entity_type"])
                            entity_groups[key].append(row)

                        header_lines = [
                            "## Entity-Document Map (from knowledge graph index)",
                            "",
                            "Each entity below lists the documents where it appears.",
                            "[PARTY_TO] = direct party/signatory to the agreement "
                            "in that document.",
                            "[---] = merely referenced (address, job site, invoice "
                            "recipient).",
                            "The context sentence after each entry shows the "
                            "entity's actual contractual role (e.g. owner, "
                            "builder, agent). Use ONLY that context to determine "
                            "roles — do NOT rely on signature-block titles.",
                            "",
                        ]
                        for (ent_name, ent_type), rows in entity_groups.items():
                            header_lines.append(f"### {ent_name} [{ent_type}]")
                            for row in rows:
                                role_labels = row.get("doc_role_labels", [])
                                role_str = (
                                    ", ".join(role_labels) if role_labels else "---"
                                )
                                snippet = self._extract_sentence_context(
                                    ent_name,
                                    row.get("doc_sample_chunk", ""),
                                )
                                doc_title = row["document_title"]
                                header_lines.append(
                                    f'- {doc_title} [{role_str}]: "{snippet}"'
                                )
                            header_lines.append("")  # blank line between entities

                        graph_structural_header = "\n".join(header_lines)

                        unique_entities = len(entity_groups)
                        logger.info(
                            "step_45_entity_doc_map_v3",
                            entity_types=detected_types,
                            rows_total=len(entity_doc_rows_raw),
                            rows_after_filter=len(entity_doc_rows),
                            unique_entities=unique_entities,
                            role_labels_removed=len(entity_doc_rows_raw) - len(entity_doc_rows),
                            query=query[:80],
                        )

        timings_ms["step_45_parallel_ms"] = int((time.perf_counter() - t0) * 1000)

        # Route 8: Inject community sentence texts directly into synthesis context.
        # PPR/reranker may filter out cross-document sentences that are relevant
        # but buried under a dominant entity cluster.  For thematic queries, we
        # fetch sentence texts from matched communities and append them as
        # additional pre_fetched_chunks so the LLM sees content from ALL relevant
        # document neighborhoods.
        community_inject_enabled = _ov(
            "community_context_inject", "ROUTE8_COMMUNITY_CONTEXT_INJECT", "1"
        ).strip().lower() in {"1", "true", "yes"}
        if community_inject_enabled and community_passage_seeds_enabled and community_sentence_ids and pre_fetched_chunks is not None:
            existing_ids = {c.get("sentence_id") or c.get("id") for c in pre_fetched_chunks}
            # Only add community sentences not already in PPR output
            community_extra_ids = [
                sid for sid in community_sentence_ids if sid not in existing_ids
            ]
            if community_extra_ids:
                try:
                    inject_cap = int(_ov("community_inject_cap", "ROUTE8_COMMUNITY_INJECT_CAP", "100"))
                    community_extra_chunks = await self._fetch_sentences_by_ids(
                        community_extra_ids[:inject_cap],
                        ppr_scores_map={sid: 0.01 for sid in community_extra_ids[:inject_cap]},
                        sentence_window_enabled=False,
                        folder_id=folder_id,
                    )
                    if community_extra_chunks:
                        pre_fetched_chunks = list(pre_fetched_chunks) + community_extra_chunks
                        # Debug: check if specific content made it
                        _has_180 = any("180" in (c.get("text","") or "") for c in community_extra_chunks)
                        logger.info(
                            "step_45b_community_context_inject",
                            ppr_chunks=len(pre_fetched_chunks) - len(community_extra_chunks),
                            community_chunks=len(community_extra_chunks),
                            total_chunks=len(pre_fetched_chunks),
                            has_180_days=_has_180,
                        )
                except Exception as e:
                    logger.warning("step_45b_community_context_inject_failed", error=str(e))

        # Step 45c: Entity embedding → 1-hop sentence injection.
        # Fetch sentences directly connected to entity-embedding-matched
        # entities and inject into synthesis context.  This is more targeted
        # than community injection (27 vs 82 chunks) and bypasses PPR
        # dilution which drowns minority-cluster entities.
        entity_inject_enabled = _ov(
            "entity_context_inject", "ROUTE8_ENTITY_CONTEXT_INJECT",
            "1" if preset.get("entity_context_inject", True) else "0"
        ).strip().lower() in {"1", "true", "yes"}
        if entity_inject_enabled and emb_entity_ids and pre_fetched_chunks is not None and self._async_neo4j:
            try:
                sent_cypher = """
                UNWIND $entity_ids AS eid
                MATCH (e:Entity {id: eid})<-[:MENTIONS]-(s:Sentence)
                WHERE s.group_id IN $group_ids
                RETURN DISTINCT s.id AS sentence_id
                """
                async with self._async_neo4j._get_session() as session:
                    sent_result = await session.run(
                        sent_cypher,
                        entity_ids=emb_entity_ids,
                        group_ids=self.group_ids,
                    )
                    sent_records = await sent_result.data()

                existing_ids = {c.get("sentence_id") or c.get("id") for c in pre_fetched_chunks}
                entity_extra_ids = [
                    r["sentence_id"] for r in sent_records
                    if r.get("sentence_id") and r["sentence_id"] not in existing_ids
                ]
                if entity_extra_ids:
                    entity_extra_chunks = await self._fetch_sentences_by_ids(
                        entity_extra_ids,
                        ppr_scores_map={sid: 0.02 for sid in entity_extra_ids},
                        sentence_window_enabled=False,
                        folder_id=folder_id,
                    )
                    if entity_extra_chunks:
                        pre_fetched_chunks = list(pre_fetched_chunks) + entity_extra_chunks
                        logger.info(
                            "step_45c_entity_context_inject",
                            entity_seeds=len(emb_entity_ids),
                            entity_sentences=len(sent_records),
                            new_chunks=len(entity_extra_chunks),
                            total_chunks=len(pre_fetched_chunks),
                        )
            except Exception as e:
                logger.warning("step_45c_entity_context_inject_failed", error=str(e))

        # Step 45d: Minimum chunks per document guarantee.
        # For global cross-doc questions, PPR may under-represent documents
        # whose entities are structurally peripheral (e.g., purchase_contract
        # getting 2 chunks while warranty gets 30).  This supplements
        # under-represented documents with evenly-spaced sentences so
        # every document's key parties/terms reach the MAP step.
        if min_chunks_per_doc > 0 and pre_fetched_chunks is not None and self._async_neo4j:
            try:
                # Count existing chunks per document
                _doc_counts: Dict[str, int] = defaultdict(int)
                _existing_ids: set = set()
                for c in pre_fetched_chunks:
                    _meta = c.get("metadata") or {}
                    did = (
                        _meta.get("document_id")
                        or c.get("document_id")
                        or ""
                    )
                    if did:
                        _doc_counts[did] += 1
                    _existing_ids.add(c.get("sentence_id") or c.get("id", ""))

                # Find all documents in the group
                _doc_cypher = """
                MATCH (s:Sentence)
                WHERE s.group_id IN $group_ids
                RETURN DISTINCT s.document_id AS doc_id, count(s) AS total
                """
                async with self._async_neo4j._get_session() as session:
                    _doc_result = await session.run(
                        _doc_cypher, group_ids=self.group_ids
                    )
                    _all_docs = await _doc_result.data()

                # Supplement under-represented docs (below min_chunks_per_doc)
                # with query-relevant chunks selected by cosine similarity.
                _target_docs = [
                    (d["doc_id"], d["total"])
                    for d in _all_docs
                    if d.get("doc_id")
                    and _doc_counts.get(d["doc_id"], 0) < min_chunks_per_doc
                ]

                if _target_docs:
                    _supplement_ids: List[str] = []
                    _need_cypher = """
                    MATCH (s:Sentence)
                    WHERE s.document_id = $doc_id
                      AND s.group_id IN $group_ids
                    RETURN s.id AS sid, s.index_in_doc AS idx,
                           s.sentence_embedding AS emb, s.text AS text
                    ORDER BY s.index_in_doc
                    """

                    def _cosine(a, b):
                        dot = sum(x * y for x, y in zip(a, b))
                        na = sum(x * x for x in a) ** 0.5
                        nb = sum(x * x for x in b) ** 0.5
                        return dot / (na * nb) if na and nb else 0.0

                    # Collect docs needing reranker-based selection
                    _rerank_batches: List[tuple] = []  # (doc_id, _need, _available)

                    async with self._async_neo4j._get_session() as session:
                        for doc_id, total in _target_docs:
                            _have = _doc_counts.get(doc_id, 0)
                            _need = min_chunks_per_doc - _have
                            if _need <= 0:
                                continue
                            _res = await session.run(
                                _need_cypher,
                                doc_id=doc_id,
                                group_ids=self.group_ids,
                            )
                            _rows = await _res.data()
                            _available = [
                                r for r in _rows
                                if r["sid"] not in _existing_ids
                            ]
                            if _available:
                                # For small docs, include ALL sentences
                                if len(_available) <= min_chunks_per_doc * 2:
                                    _supplement_ids.extend(
                                        r["sid"] for r in _available
                                    )
                                else:
                                    _rerank_batches.append(
                                        (doc_id, _need, _available)
                                    )

                    # Use reranker for larger docs — it bridges semantic
                    # gaps that cosine misses (e.g. "cancel for refund"
                    # as a "remedy").  Falls back to cosine on failure.
                    if _rerank_batches:
                        try:
                            _vc = make_voyage_client()
                            for _doc_id, _need, _avail in _rerank_batches:
                                _texts = [
                                    r.get("text") or "" for r in _avail
                                ]
                                _rr = await rerank_with_retry(
                                    _vc,
                                    query=query,
                                    documents=_texts,
                                    model="rerank-2.5",
                                    top_k=min(
                                        _need + min_chunks_per_doc,
                                        len(_texts),
                                    ),
                                )
                                _picks = [
                                    _avail[rr_item.index]
                                    for rr_item in _rr.results
                                ][:_need + min_chunks_per_doc]
                                _supplement_ids.extend(
                                    r["sid"] for r in _picks
                                )
                                logger.info(
                                    "step_45d_rerank_supplement",
                                    doc_id=_doc_id[:12],
                                    candidates=len(_avail),
                                    selected=len(_picks),
                                    top_score=round(
                                        _rr.results[0].relevance_score, 3
                                    ) if _rr.results else 0,
                                )
                        except Exception as _rr_err:
                            logger.warning(
                                "step_45d_rerank_fallback_to_cosine",
                                error=str(_rr_err),
                            )
                            # Fallback: cosine selection
                            for _doc_id, _need, _avail in _rerank_batches:
                                for row in _avail:
                                    emb = row.get("emb")
                                    row["_sim"] = (
                                        _cosine(query_embedding, emb)
                                        if emb else 0.0
                                    )
                                _avail.sort(key=lambda r: -r["_sim"])
                                _supplement_ids.extend(
                                    r["sid"] for r in _avail[:_need]
                                )

                    if _supplement_ids:
                        _supp_chunks = await self._fetch_sentences_by_ids(
                            _supplement_ids,
                            ppr_scores_map={
                                sid: 0.005 for sid in _supplement_ids
                            },
                            sentence_window_enabled=False,
                            folder_id=folder_id,
                        )
                        if _supp_chunks:
                            pre_fetched_chunks = list(pre_fetched_chunks) + _supp_chunks
                            logger.info(
                                "step_45d_min_chunks_per_doc",
                                min_per_doc=min_chunks_per_doc,
                                docs_supplemented=len(_target_docs),
                                supplement_chunks=len(_supp_chunks),
                                total_chunks=len(pre_fetched_chunks),
                            )
            except Exception as e:
                logger.warning("step_45d_min_chunks_per_doc_failed", error=str(e))

        # ── Step 45e: Section-coverage guarantee ──────────────────────
        # Ensure query-relevant sections from represented documents are
        # not silently dropped.  PPR may retrieve many sentences from
        # high-entity sections while missing isolated sections with
        # few/no entities (e.g., "Right to Cancel").  We collect one
        # sentence from each unrepresented section, then use the
        # reranker to keep only those relevant to the query.
        if min_chunks_per_doc > 0 and pre_fetched_chunks is not None and self._async_neo4j:
            try:
                _sec_doc_ids: set = set()
                _sec_existing: set = set()
                for c in pre_fetched_chunks:
                    _meta = c.get("metadata") or {}
                    did = _meta.get("document_id") or c.get("document_id") or ""
                    if did:
                        _sec_doc_ids.add(did)
                    _sec_existing.add(c.get("sentence_id") or c.get("id", ""))

                if _sec_doc_ids:
                    _sec_cypher = """
                    MATCH (sent:Sentence)-[:IN_SECTION]->(sec:Section)
                    WHERE sent.document_id = $doc_id
                      AND sent.group_id IN $group_ids
                    RETURN sec.title AS section, sent.id AS sid,
                           sent.text AS text
                    ORDER BY sec.title, sent.index_in_section
                    """
                    # Candidate sentences (one per missing section)
                    _sec_candidates: List[Dict] = []
                    async with self._async_neo4j._get_session() as session:
                        for did in _sec_doc_ids:
                            _res = await session.run(
                                _sec_cypher, doc_id=did,
                                group_ids=self.group_ids,
                            )
                            _rows = await _res.data()
                            _by_sec: Dict[str, List[Dict]] = defaultdict(list)
                            for r in _rows:
                                _by_sec[r["section"]].append(r)
                            for sec_title, sec_sents in _by_sec.items():
                                has_rep = any(
                                    s["sid"] in _sec_existing
                                    for s in sec_sents
                                )
                                if not has_rep and sec_sents:
                                    # Small sections (≤3 sentences): add all
                                    # so reranker can pick the most relevant.
                                    # Larger sections: just the first sentence.
                                    if len(sec_sents) <= 3:
                                        _sec_candidates.extend(sec_sents)
                                    else:
                                        _sec_candidates.append(sec_sents[0])
                                elif has_rep and len(sec_sents) <= 3:
                                    # Section completion: tiny sections that
                                    # are partially represented — add missing
                                    # sentences so MAP sees full context.
                                    for s in sec_sents:
                                        if s["sid"] not in _sec_existing:
                                            _sec_candidates.append(s)

                    # Reranker filter: keep only sections the reranker
                    # scores above threshold (semantic relevance to query).
                    _sec_supplement: List[str] = []
                    _sec_rerank_threshold = 0.30
                    _sec_max_add = 5
                    if _sec_candidates:
                        try:
                            _sec_vc = make_voyage_client()
                            _sec_texts = [
                                c.get("text") or "" for c in _sec_candidates
                            ]
                            _sec_rr = await rerank_with_retry(
                                _sec_vc,
                                query=query,
                                documents=_sec_texts,
                                model="rerank-2.5",
                                top_k=len(_sec_texts),
                            )
                            for rr_item in _sec_rr.results:
                                if (rr_item.relevance_score >= _sec_rerank_threshold
                                        and len(_sec_supplement) < _sec_max_add):
                                    _sec_supplement.append(
                                        _sec_candidates[rr_item.index]["sid"]
                                    )
                            logger.info(
                                "step_45e_rerank_filter",
                                candidates=len(_sec_candidates),
                                kept=len(_sec_supplement),
                                threshold=_sec_rerank_threshold,
                                top_score=round(
                                    _sec_rr.results[0].relevance_score, 3
                                ) if _sec_rr.results else 0,
                            )
                        except Exception as _rr_err:
                            logger.warning(
                                "step_45e_rerank_failed_adding_all",
                                error=str(_rr_err),
                            )
                            _sec_supplement = [
                                c["sid"] for c in _sec_candidates
                            ]

                    if _sec_supplement:
                        _sec_chunks = await self._fetch_sentences_by_ids(
                            _sec_supplement,
                            ppr_scores_map={
                                sid: 0.004 for sid in _sec_supplement
                            },
                            sentence_window_enabled=False,
                            folder_id=folder_id,
                        )
                        if _sec_chunks:
                            pre_fetched_chunks = list(pre_fetched_chunks) + _sec_chunks
                            logger.info(
                                "step_45e_section_coverage",
                                sections_added=len(_sec_chunks),
                                total_chunks=len(pre_fetched_chunks),
                            )
            except Exception as e:
                logger.warning("step_45e_section_coverage_failed", error=str(e))

        # Convert sentence evidence to coverage_chunks format
        sentence_chunks: List[Dict[str, Any]] = []
        if sentence_evidence:
            for ev in sentence_evidence:
                sentence_chunks.append({
                    "text": ev.get("text", ""),
                    "document_title": ev.get("document_title", "Unknown"),
                    "document_id": ev.get("document_id", ""),
                    "section_path": ev.get("section_path", ""),
                    "page_number": ev.get("page"),
                    "_entity_score": ev.get("score", 0.5),
                    "_source_entity": "__sentence_search__",
                })

        # Use entity_scores as evidence_nodes for the synthesizer
        evidence_nodes = entity_scores[:20]

        t0 = time.perf_counter()

        # ------------------------------------------------------------------
        # Step 5: Synthesis — per-document map-reduce OR single-shot
        # ------------------------------------------------------------------
        all_chunks = list(pre_fetched_chunks or [])
        if sentence_chunks:
            all_chunks.extend(sentence_chunks)

        if map_reduce_synthesis and all_chunks:
            synthesis_result = await self._map_reduce_synthesize(
                query=query,
                chunks=all_chunks,
                evidence_nodes=evidence_nodes,
                prompt_variant=prompt_variant,
                synthesis_model=synthesis_model,
                include_context=include_context,
                language=language,
                max_tokens=synthesis_max_tokens,
                concurrency=map_reduce_concurrency,
                graph_structural_header=graph_structural_header,
            )
        else:
            synthesis_result = await self.pipeline.synthesizer.synthesize(
                query=query,
                evidence_nodes=evidence_nodes,
                response_type=response_type,
                coverage_chunks=sentence_chunks if sentence_chunks else None,
                prompt_variant=prompt_variant,
                synthesis_model=synthesis_model,
                include_context=include_context,
                pre_fetched_chunks=pre_fetched_chunks,
                graph_structural_header=graph_structural_header,
                language=language,
                max_tokens=synthesis_max_tokens,
            )

        timings_ms["step_5_synthesis_ms"] = int((time.perf_counter() - t0) * 1000)
        timings_ms["total_ms"] = int((time.perf_counter() - t_route_start) * 1000)

        logger.info(
            "step_5_synthesis_complete",
            response_length=len(synthesis_result.get("response", "")),
            text_chunks_used=synthesis_result.get("text_chunks_used", 0),
            total_ms=timings_ms["total_ms"],
            map_reduce=map_reduce_synthesis,
        )

        # ------------------------------------------------------------------
        # Step 6: Build citations
        # ------------------------------------------------------------------
        citations: List[Citation] = []
        for i, c in enumerate(synthesis_result.get("citations", []), 1):
            if isinstance(c, dict):
                meta = c.get("metadata") or {}
                section_path = (
                    meta.get("section_path")
                    or meta.get("section_path_key")
                    or c.get("section_path", "")
                )
                if isinstance(section_path, list):
                    section_path = " > ".join(str(s) for s in section_path if s)
                citations.append(
                    Citation(
                        index=i,
                        sentence_id=c.get("chunk_id", f"chunk_{i}"),
                        document_id=c.get("document_id", ""),
                        document_title=c.get("document_title", c.get("document", "Unknown")),
                        document_url=c.get("document_url", "") or c.get("document_source", "") or meta.get("url", ""),
                        page_number=c.get("page_number") or meta.get("page_number"),
                        section_path=section_path,
                        start_offset=c.get("start_offset") or meta.get("start_offset"),
                        end_offset=c.get("end_offset") or meta.get("end_offset"),
                        score=c.get("score", 0.0),
                        text_preview=c.get("text_preview", c.get("text", ""))[:200],
                        sentences=c.get("sentences"),
                        page_dimensions=c.get("page_dimensions"),
                        citation_key=c.get("citation", ""),
                        source=c.get("source", ""),
                        citation_type=c.get("citation_type", "chunk"),
                    )
                )

        # Post-synthesis: narrow chunk citations to specific sentences
        sentence_map = synthesis_result.get("sentence_citation_map", {})
        if sentence_map:
            self._narrow_citations_to_sentences(
                citations, synthesis_result.get("response", ""), sentence_map
            )
        await self._enrich_citations_with_geometry(citations)

        # Diagnostic: log citation geometry state for debugging highlight issues
        for _ci, _cit in enumerate(citations):
            _poly_count = len(_cit.sentences) if _cit.sentences else 0
            _total_polys = sum(
                len(sp.get("polygons", [])) if isinstance(sp, dict) else 0
                for sp in (_cit.sentences or [])
            )
            logger.info(
                "citation_geometry_debug",
                query_mode=query_mode,
                sentence_window=sentence_window_enabled,
                citation_index=_cit.index,
                sentence_id=_cit.sentence_id,
                text_preview_len=len(_cit.text_preview or ""),
                text_preview_snippet=(_cit.text_preview or "")[:80],
                has_sentences=bool(_cit.sentences),
                sentence_spans=_poly_count,
                total_polygons=_total_polys,
                has_page_dimensions=bool(_cit.page_dimensions),
                page_number=_cit.page_number,
            )

        # ------------------------------------------------------------------
        # Assemble metadata
        # ------------------------------------------------------------------
        metadata: Dict[str, Any] = {
            "architecture": "hipporag2",
            "damping": ppr_damping,
            "triple_top_k": triple_top_k,
            "surviving_triples": len(surviving_triples),
            "entity_seeds_count": len(entity_seeds),
            "passage_seeds_count": len(passage_seeds),
            "passage_node_weight": passage_node_weight,
            "num_ppr_passages": len(top_passage_scores),
            "num_ppr_entities": len(entity_scores[:20]),
            "text_chunks_used": synthesis_result.get("text_chunks_used", 0),
            "sentence_evidence_count": len(sentence_evidence),
            "route_description": "True HippoRAG 2 with passage-node PPR (v7)",
            "version": "v7.4",
            "rerank_enabled": rerank_enabled,
            "rerank_all_enabled": rerank_all_enabled,
            "rerank_all_injected": rerank_all_injected,
            "semantic_passage_seeds_enabled": semantic_passage_seeds_enabled,
            "semantic_seeds_added": semantic_seeds_added,
            "neural_weight": neural_weight,
            "llm_filter_enabled": llm_filter_enabled,
            "llm_filter_removed": llm_filter_removed,
            "query_mode": query_mode,
            "query_mode_preset_applied": query_mode in self.QUERY_MODE_PRESETS if query_mode else False,
        }

        # Phase 2 metadata
        if structural_seeds_enabled:
            metadata["structural_sections"] = structural_sections
        if community_data:
            metadata["matched_communities"] = [
                c.get("title", "?") for c in community_data[:5]
            ]
        metadata["community_passage_seeds_added"] = community_seeds_added
        metadata["triple_entity_ids_count"] = len(triple_entity_ids)

        # Entity-doc map metadata
        if graph_structural_header:
            metadata["entity_doc_map"] = {
                "entity_types": detected_types,
                "entities_found": len(entity_doc_rows),
            }

        # Triple details
        metadata["triple_seeds"] = [
            t.triple_text for t, _s in surviving_triples[:10]
        ]

        if include_context:
            _ppr_text_map = self._ppr_engine.get_all_passage_texts()
            metadata["ppr_top_passages"] = [
                {
                    "sentence_id": cid,
                    "score": round(s, 6),
                    "text": (_ppr_text_map.get(cid, ""))[:400],
                }
                for cid, s in raw_ppr_passage_scores[:ppr_passage_top_k]
            ]
            metadata["final_passages"] = [
                {
                    "sentence_id": cid,
                    "score": round(s, 6),
                    "text": (_ppr_text_map.get(cid, ""))[:400],
                }
                for cid, s in top_passage_scores
            ]
            metadata["ppr_top_entities"] = [
                {"entity": name, "score": round(s, 6)}
                for name, s in entity_scores[:10]
            ]
            if synthesis_result.get("context_stats"):
                metadata["context_stats"] = synthesis_result["context_stats"]
            if synthesis_result.get("llm_context"):
                metadata["llm_context"] = synthesis_result["llm_context"]

        if synthesis_result.get("raw_extractions"):
            metadata["raw_extractions"] = synthesis_result["raw_extractions"]
        if synthesis_result.get("processing_mode"):
            metadata["processing_mode"] = synthesis_result["processing_mode"]

        if enable_timings:
            metadata["timings_ms"] = timings_ms

        # Debug: citation geometry summary in response metadata
        metadata["_citation_debug"] = {
            "query_mode": query_mode,
            "sentence_window_enabled": sentence_window_enabled,
            "citations": [
                {
                    "idx": ct.index,
                    "sid": ct.sentence_id,
                    "text_len": len(ct.text_preview or ""),
                    "text_snippet": (ct.text_preview or "")[:60],
                    "has_sentences": bool(ct.sentences),
                    "polygon_count": sum(
                        len(sp.get("polygons", []))
                        if isinstance(sp, dict) else 0
                        for sp in (ct.sentences or [])
                    ),
                    "sentence_texts": [
                        (sp.get("text", "") or "")[:60]
                        for sp in (ct.sentences or [])
                        if isinstance(sp, dict)
                    ][:3],
                    "has_page_dims": bool(ct.page_dimensions),
                    "page": ct.page_number,
                }
                for ct in citations
            ],
        }

        return RouteResult(
            response=synthesis_result.get("response", ""),
            route_used=self.ROUTE_NAME,
            citations=citations,
            evidence_path=[name for name, _ in entity_scores[:20]]
            + [
                {
                    "sentence_id": c["id"],
                    "text": (c.get("text") or "")[:200],
                    "document_title": c.get("source", ""),
                    "ppr_score": round(c.get("_ppr_score", 0.0), 6),
                }
                for c in (pre_fetched_chunks or [])[:10]
            ],
            metadata=metadata,
            usage=synthesis_result.get("usage"),
            timing=(
                {"total_ms": timings_ms.get("total_ms", 0)}
                if enable_timings
                else None
            ),
        )

    # ======================================================================
    # Helper: Empty result
    # ======================================================================

    def _empty_result(self, reason: str) -> RouteResult:
        """Return a negative-detection RouteResult."""
        return RouteResult(
            response="The requested information was not found in the available documents.",
            route_used=self.ROUTE_NAME,
            citations=[],
            evidence_path=[],
            metadata={
                "negative_detection": True,
                "detection_reason": reason,
            },
        )

    # ======================================================================
    # Entity-doc map v2: exhaustive entity enumeration
    # ======================================================================

    @staticmethod
    def _detect_exhaustive_entity_types(query: str) -> Optional[List[str]]:
        """Detect if query requires exhaustive entity enumeration.

        Returns a list of entity type strings (e.g. ["ORGANIZATION", "PERSON"])
        when the query has exhaustive intent + corpus scope + a detectable type
        target.  Returns None otherwise (normal pipeline runs unchanged).

        Three gates keep false-positive rate low:
          1. Exhaustive intent — list/enumerate/find + all/every/each/across
          2. Corpus scope — mentions documents/contracts/files/set
          3. Type target — maps query-object words to entity type schema
        """
        q = query.lower()

        if not _EXHAUSTIVE_INTENT_RE.search(q):
            return None

        if not _CORPUS_SCOPE_RE.search(q):
            return None

        matched_types: set = set()
        for entity_type, keywords in _ENTITY_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in q:
                    matched_types.add(entity_type)

        return sorted(matched_types) if matched_types else None

    @staticmethod
    def _extract_sentence_context(
        entity_name: str, chunk_text: str, max_chars: int = 500
    ) -> str:
        """Extract a 3-sentence window around the entity mention.

        Finds the sentence containing the entity, then includes ±1
        adjacent sentences for anaphora and role context.  Returns the
        window capped at *max_chars*.  Falls back to the first
        *max_chars* of the chunk when the entity is not found.
        """
        if not chunk_text:
            return ""

        idx = chunk_text.lower().find(entity_name.lower())
        if idx < 0:
            return chunk_text[:max_chars].strip()

        # ── Split chunk into sentences ──
        import re
        # Split on sentence-ending punctuation followed by whitespace
        sent_spans: list[tuple[int, int]] = []
        for m in re.finditer(r'[^.!?\n]+(?:[.!?]+|\n|$)', chunk_text):
            s, e = m.start(), m.end()
            if m.group().strip():
                sent_spans.append((s, e))

        if not sent_spans:
            return chunk_text[:max_chars].strip()

        # Find which sentence contains the entity
        target_idx = 0
        for i, (s, e) in enumerate(sent_spans):
            if s <= idx < e:
                target_idx = i
                break

        # ±1 sentence window
        win_start = max(0, target_idx - 1)
        win_end = min(len(sent_spans), target_idx + 2)

        window_text = chunk_text[
            sent_spans[win_start][0]:sent_spans[win_end - 1][1]
        ].strip()

        # Truncate if too long, keeping entity visible
        if len(window_text) > max_chars:
            entity_pos = idx - sent_spans[win_start][0]
            half = max_chars // 2
            t_start = max(0, entity_pos - half)
            t_end = min(len(window_text), t_start + max_chars)
            original_len = len(window_text)
            window_text = window_text[t_start:t_end].strip()
            if t_start > 0:
                window_text = "..." + window_text
            if t_end < original_len:
                window_text = window_text + "..."

        return window_text

    async def _query_entity_doc_map(
        self,
        entity_types: List[str],
        folder_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query ALL entities of given types with per-document granularity.

        Returns one row per (entity, document) pair, each with:
        - doc_mentions: how many TextChunks mention this entity in this doc
        - doc_sample_chunk: a sample chunk from THIS document (not global)
        - doc_role_labels: RELATED_TO role types scoped to this document
          (only includes roles where the related entity also appears
          in the same document)

        Uses the MENTIONS + IN_DOCUMENT edge path — the same structural
        index that PPR traverses, but without PPR's top-K scope limitation.
        """
        if not entity_types or not self.neo4j_driver:
            return []

        group_ids = self.group_ids
        cypher = """
        MATCH (e:Entity)
              <-[:MENTIONS]-(tc:Sentence)
              -[:IN_DOCUMENT]->(d:Document)
        WHERE e.group_id IN $group_ids
          AND tc.group_id IN $group_ids
          AND d.group_id IN $group_ids
          AND e.type IN $entity_types
        WITH e, d, count(tc) AS doc_mentions,
             collect(tc.text)[0] AS doc_sample_chunk
        OPTIONAL MATCH (e)-[r:RELATED_TO]-(e2:Entity)
        WHERE e2.group_id IN $group_ids
          AND r.rel_type IN $role_rel_types
          AND EXISTS {
            MATCH (e2)<-[:MENTIONS]-(s2:Sentence)
                  -[:IN_DOCUMENT]->(d)
            WHERE s2.group_id IN $group_ids
          }
        WITH e, d, doc_mentions, doc_sample_chunk,
             collect(DISTINCT r.rel_type)[0..3] AS doc_role_labels
        RETURN e.name AS entity_name, e.type AS entity_type,
               d.title AS document_title, doc_mentions,
               doc_sample_chunk, doc_role_labels
        ORDER BY entity_name, doc_mentions DESC
        """
        driver = self.neo4j_driver

        def _run():
            with retry_session(driver, read_only=True) as session:
                records = session.run(
                    cypher,
                    group_ids=group_ids,
                    entity_types=entity_types,
                    role_rel_types=_STRUCTURED_ROLE_TYPES,
                    folder_id=folder_id,
                )
                return [
                    {
                        "entity_name": r["entity_name"],
                        "entity_type": r["entity_type"],
                        "document_title": r["document_title"] or "",
                        "doc_mentions": r["doc_mentions"],
                        "doc_sample_chunk": r["doc_sample_chunk"] or "",
                        "doc_role_labels": [
                            rl for rl in (r["doc_role_labels"] or []) if rl
                        ],
                    }
                    for r in records
                ]

        try:
            results = await asyncio.to_thread(_run)
            logger.info(
                "route7_entity_doc_map_v3",
                entity_types=entity_types,
                rows_found=len(results),
            )
            return results
        except Exception as e:
            logger.warning("route7_entity_doc_map_v3_failed", error=str(e))
            return []

    # ======================================================================
    # Query-to-Triple Linking + Recognition Memory
    # ======================================================================

    async def _query_to_triple_linking(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple]:
        """Three-stage triple funnel: instructed cosine → reranker → MMR.

        Returns list of (Triple, score) tuples with relevance scores.

        Pipeline:
          Stage 1: Instructed voyage-context-3 cosine search (N → 500 candidates)
          Stage 2: Voyage rerank-2.5 cross-encoder (500 → 15 precision-ranked)
          Stage 3: MMR diversity filter (15 → ≤7 deduplicated facts)

        When ROUTE7_TRIPLE_SEARCH_INSTRUCTION is set (default: enabled), the
        cosine search uses an instruction-prefixed query embedding via
        voyage-context-3.  This steers the embedding toward temporal/numeric
        semantics, dramatically improving recall for enumeration queries like
        "list all day-based timeframes" where bare cosine matches literal
        words (e.g. "windows" in "time windows") instead of the intent.
        """
        from ..retrievers.triple_store import mmr_diversity_filter, recognition_memory_filter

        # --- Instructed embedding for triple cosine search ----------------
        triple_instruction = os.getenv(
            "ROUTE7_TRIPLE_SEARCH_INSTRUCTION",
            "Identify every fact mentioning a numeric time period, duration, "
            "fee, obligation, condition, or named entity relevant to this query. "
            "Query: ",
        ).strip()

        if triple_instruction:
            from src.core.config import settings

            instructed_text = f"{triple_instruction}{query}"
            try:
                vc = make_voyage_client()
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: vc.contextualized_embed(
                        inputs=[[instructed_text]],
                        model=settings.VOYAGE_MODEL_NAME,
                        input_type="query",
                        output_dimension=settings.VOYAGE_EMBEDDING_DIM,
                    ),
                )
                search_embedding = result.results[0].embeddings[0]
                logger.debug(
                    "route7_triple_instructed_embedding",
                    instruction_len=len(triple_instruction),
                )
            except Exception as e:
                logger.warning("route7_triple_instructed_embed_failed", error=str(e))
                search_embedding = query_embedding
        else:
            search_embedding = query_embedding

        # Stage 1: Widen cosine search when triple reranking is enabled
        triple_rerank = os.getenv(
            "ROUTE7_TRIPLE_RERANK", "1"
        ).strip().lower() in {"1", "true", "yes"}
        candidates_k = int(os.getenv("ROUTE7_TRIPLE_CANDIDATES_K", "500"))
        fetch_k = candidates_k if triple_rerank else top_k

        candidates = self._triple_store.search(search_embedding, top_k=fetch_k)

        if not candidates:
            logger.info("route7_no_triple_candidates", query=query[:60])
            return []

        logger.debug(
            "route7_triple_candidates",
            count=len(candidates),
            top_scores=[round(s, 4) for _, s in candidates[:5]],
        )

        # Stage 2: Instruction-following reranking with Voyage rerank-2.5
        if triple_rerank and len(candidates) > top_k:
            candidates = await self._rerank_triples(query, candidates, top_k=top_k)

        # Stage 3: Diversity filter (MMR or legacy LLM recognition memory)
        recognition_mode = os.getenv("ROUTE7_RECOGNITION_MEMORY_MODE", "mmr").strip().lower()

        if recognition_mode == "mmr":
            from ..retrievers.triple_store import mmr_diversity_filter
            surviving = mmr_diversity_filter(candidates)
        else:
            # Legacy LLM-based recognition memory filter
            llm_client = getattr(self.pipeline.disambiguator, "llm", None)
            if not llm_client:
                logger.warning("route7_no_llm_for_recognition_memory")
                return list(candidates)
            surviving = await recognition_memory_filter(llm_client, query, candidates)

        return surviving

    async def _rerank_triples(
        self,
        query: str,
        candidates: List[Tuple],
        top_k: int = 5,
    ) -> List[Tuple]:
        """Rerank triple candidates using Voyage rerank-2.5.

        Prepends an instruction to the query to steer the cross-encoder
        toward abstract category membership (e.g., "time windows" → "3 business days").
        """
        rerank_model = os.getenv("ROUTE7_RERANK_MODEL", "rerank-2.5")
        documents = [triple.triple_text for triple, _ in candidates]

        # Prepend instruction to query to guide reranker scoring
        instructed_query = (
            "Identify facts relevant to answering this query. "
            "Consider abstract category membership — e.g., specific durations "
            "like '3 business days' or '90 days' are relevant to 'timeframes'. "
            f"Query: {query}"
        )

        try:
            vc = make_voyage_client()
            rr_result = await rerank_with_retry(
                vc, query=instructed_query, documents=documents,
                model=rerank_model, top_k=min(top_k, len(documents)),
            )

            # Map results back to (Triple, rerank_score) tuples
            reranked = [
                (candidates[rr.index][0], rr.relevance_score)
                for rr in rr_result.results
            ]

            logger.info(
                "route7_triple_rerank_complete",
                model=rerank_model,
                input=len(documents),
                output=len(reranked),
                top_score=round(reranked[0][1], 4) if reranked else 0,
                top_triple=reranked[0][0].triple_text[:60] if reranked else "",
            )

            # Track usage
            try:
                _total = getattr(rr_result, "total_tokens", 0)
                acc = getattr(self, "_token_accumulator", None)
                if acc is not None:
                    acc.add_rerank(rerank_model, _total, len(documents))
            except Exception:
                pass

            return reranked

        except Exception as e:
            logger.warning("route7_triple_rerank_failed", error=str(e))
            return candidates[:top_k]

    # ======================================================================
    # DPR Passage Search (Small-to-Big: sentence → parent chunk)
    # ======================================================================

    async def _dpr_passage_search(
        self,
        query_embedding: List[float],
        top_k: int = 0,
        sentence_top_k: int = 0,
        folder_id: Optional[str] = None,
    ) -> List[Tuple[str, float]]:
        """Dense Passage Retrieval via sentence-level vector search.

        Searches sentence_embedding for sharp single-sentence matches.
        Returns sentence IDs as passage nodes for PPR.

        When top_k=-1, DPR is disabled (cross-encoder seeds outperform at small scale).
        When top_k=0 (upstream-aligned), queries the corpus size
        first so ALL passages are returned and seeded into PPR.
        """
        if top_k < 0:
            return []
        if not self.neo4j_driver:
            return []

        group_ids = self.group_ids
        folder_id = folder_id if folder_id is not None else self.folder_id
        driver = self.neo4j_driver

        # When top_k=0, resolve actual corpus size so we seed all passages
        if top_k <= 0 or sentence_top_k <= 0:
            count_cypher = """CYPHER 25
            MATCH (s:Sentence)
            WHERE s.group_id IN $group_ids
            RETURN count(s) AS cnt
            """
            try:
                def _count():
                    with retry_session(driver, read_only=True) as session:
                        return session.run(count_cypher, group_ids=group_ids).single()["cnt"]
                corpus_size = await asyncio.to_thread(_count)
            except Exception:
                corpus_size = 200  # safe fallback
            if top_k <= 0:
                top_k = corpus_size
            if sentence_top_k <= 0:
                sentence_top_k = corpus_size

        sentence_cypher = """CYPHER 25
        CALL () {
            MATCH (s:Sentence)
            SEARCH s IN (VECTOR INDEX sentence_embedding FOR $embedding WHERE s.group_id = $group_id LIMIT $sentence_top_k)
            SCORE AS score
            RETURN s, score
            UNION ALL
            MATCH (s:Sentence)
            SEARCH s IN (VECTOR INDEX sentence_embedding FOR $embedding WHERE s.group_id = $global_group_id LIMIT $sentence_top_k)
            SCORE AS score
            RETURN s, score
        }
        WITH s, max(score) AS score
        OPTIONAL MATCH (s)-[:IN_DOCUMENT]->(d:Document)
        WHERE d.group_id IN $group_ids
        RETURN s.id AS sentence_id, score
        ORDER BY score DESC
        LIMIT $top_k
        """

        try:
            def _run_sentence():
                with retry_session(driver, read_only=True) as session:
                    records = session.run(
                        sentence_cypher,
                        embedding=query_embedding,
                        group_id=self.group_id,
                        global_group_id=settings.GLOBAL_GROUP_ID,
                        group_ids=group_ids,
                        sentence_top_k=sentence_top_k,
                        top_k=top_k,
                        folder_id=folder_id,
                    )
                    return [(r["sentence_id"], r["score"]) for r in records]

            results = await asyncio.to_thread(_run_sentence)
            logger.debug("route7_dpr_sentence_complete", hits=len(results),
                         corpus_size=top_k)
            return results
        except Exception as e:
            logger.warning("route7_dpr_failed", error=str(e))
            return []

    # ======================================================================
    # Fetch Sentence Texts by IDs
    # ======================================================================

    async def _fetch_sentences_by_ids(
        self,
        sentence_ids: List[str],
        ppr_scores_map: Optional[Dict[str, float]] = None,
        entity_names: Optional[List[str]] = None,
        sentence_window_enabled: Optional[bool] = None,
        folder_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch sentence text + metadata from Neo4j by sentence IDs.

        Uses single-sentence ``node.text`` as synthesis context.  When
        *entity_names* is provided, builds focused 3-sentence windows
        around sentences that mention those entities (via graph MENTIONS
        edges), falling back to full sentence text otherwise.

        When *sentence_window_enabled* is ``False``, the ±1 neighbour
        expansion is skipped — useful for local_search where retrieved
        sentences are already concise and widening would dilute citations.

        Returns flat list of sentence dicts in the format expected by the
        synthesizer's ``pre_fetched_chunks`` parameter, sorted by PPR
        score descending when ``ppr_scores_map`` is provided.
        """
        if not sentence_ids or not self.neo4j_driver:
            return []

        group_ids = self.group_ids
        driver = self.neo4j_driver

        # ── Pass 1: Sentence metadata (with ±1 window via NEXT_IN_SECTION) ──
        if sentence_window_enabled is None:
            sentence_window_enabled = os.getenv(
                "ROUTE7_SENTENCE_WINDOW", "1"
            ).strip().lower() in {"1", "true", "yes"}

        cypher_sentences = """
        UNWIND $sentence_ids AS cid
        MATCH (node:Sentence {id: cid})
        WHERE node.group_id IN $group_ids
        OPTIONAL MATCH (node)-[:IN_DOCUMENT]->(d:Document)
        WHERE d.group_id IN $group_ids
        OPTIONAL MATCH (node)-[:IN_SECTION]->(s:Section)
        OPTIONAL MATCH (node)-[:NEXT_IN_SECTION]->(next_sent:Sentence)
        OPTIONAL MATCH (prev_sent:Sentence)-[:NEXT_IN_SECTION]->(node)
        RETURN cid AS sentence_id,
               coalesce(node.text, '') AS text,
               coalesce(node.index_in_doc, 0) AS index_in_doc,
               node.hierarchical_id AS hierarchical_id,
               node.page AS page,
               d.id AS document_id, d.title AS document_title,
               d.source AS document_source,
               s.title AS section_title, s.id AS section_id,
               prev_sent.text AS prev_text, prev_sent.id AS prev_id,
               next_sent.text AS next_text, next_sent.id AS next_id
        """

        folder_id = folder_id if folder_id is not None else self.folder_id

        try:
            def _run():
                with retry_session(driver, read_only=True) as session:
                    records = session.run(
                        cypher_sentences,
                        sentence_ids=sentence_ids,
                        group_ids=group_ids,
                        folder_id=folder_id,
                    )
                    return [dict(r) for r in records]
            results = await asyncio.to_thread(_run)
        except Exception as e:
            logger.warning("route7_fetch_chunks_failed", error=str(e))
            return []

        scores = ppr_scores_map or {}

        # ── Merge contiguous runs + ±1 sentence window expansion ──
        from collections import defaultdict

        retrieved_ids = {r.get("sentence_id", "") for r in results}

        section_groups: dict[tuple, list] = defaultdict(list)
        for r in results:
            key = (r.get("document_id", ""), r.get("section_title", ""))
            section_groups[key].append(r)

        merged_results: list[dict] = []
        for _key, group in section_groups.items():
            group.sort(key=lambda x: x.get("index_in_doc", 0))

            # Detect contiguous runs using hierarchical_id section prefix.
            # When sentence_window is disabled (local_search), skip merging
            # so each sentence stays a separate citation — keeps table-row
            # and element-level citations precise.
            if not sentence_window_enabled:
                runs = [[r] for r in group]
            else:
                runs = []
                current_run = [group[0]]
                for r in group[1:]:
                    prev = current_run[-1]
                    prev_idx = prev.get("index_in_doc", 0)
                    curr_idx = r.get("index_in_doc", 0)
                    prev_sec = (prev.get("hierarchical_id") or "").rsplit("-S", 1)[0]
                    curr_sec = (r.get("hierarchical_id") or "").rsplit("-S", 1)[0]
                    same_section = (prev_sec == curr_sec) and bool(prev_sec)
                    if same_section and curr_idx == prev_idx + 1:
                        current_run.append(r)
                    else:
                        runs.append(current_run)
                        current_run = [r]
                runs.append(current_run)

                # Cap run length to prevent merging entire tables into one
                # citation.  The ±1 window still provides context at the
                # edges of each sub-run.  Default 2 matches the original
                # _MAX_MERGE=2 that was proven in production.
                max_run = int(os.getenv("ROUTE7_MAX_MERGE_RUN", "1"))
                if max_run > 0:
                    capped: list[list[dict]] = []
                    for run in runs:
                        for i in range(0, len(run), max_run):
                            capped.append(run[i:i + max_run])
                    runs = capped

            for run in runs:
                first, last = run[0], run[-1]
                all_ids = [r.get("sentence_id", "") for r in run]

                # Assemble passage text
                parts: list[str] = []
                if sentence_window_enabled:
                    # Prepend prev of first sentence (section-bounded,
                    # skip if it is itself a retrieved sentence to avoid
                    # duplication across passages)
                    prev_txt = (first.get("prev_text") or "").strip()
                    prev_id = first.get("prev_id") or ""
                    if prev_txt and prev_id not in retrieved_ids:
                        parts.append(prev_txt)

                for r in run:
                    parts.append((r.get("text") or "").strip())

                if sentence_window_enabled:
                    # Append next of last sentence (same rules)
                    next_txt = (last.get("next_text") or "").strip()
                    next_id = last.get("next_id") or ""
                    if next_txt and next_id not in retrieved_ids:
                        parts.append(next_txt)

                passage = " ".join(p for p in parts if p)

                merged_result = dict(first)
                merged_result["text"] = passage
                merged_result["_merged_ids"] = all_ids
                merged_results.append(merged_result)

        chunks_list: List[Dict[str, Any]] = []
        for r in merged_results:
            cid = r.get("sentence_id", "")
            merged_ids = r.get("_merged_ids", [cid])
            best_score = max(scores.get(mid, 0.0) for mid in merged_ids) if scores else 0.0

            _doc_title = r.get("document_title", "Unknown")
            chunks_list.append({
                "id": cid,
                "source": _doc_title,
                "document_title": _doc_title,
                "text": r.get("text", ""),
                "entity": "__ppr_passage__",
                "_entity_score": 1.0,
                "_source_entity": "__ppr_passage__",
                "_ppr_score": best_score,
                "document_source": r.get("document_source", ""),
                "page_number": r.get("page"),
                "metadata": {
                    "document_id": r.get("document_id", ""),
                    "document_title": _doc_title,
                    "section_path": r.get("section_title", ""),
                    "page_number": r.get("page"),
                    "index_in_doc": r.get("index_in_doc", 0),
                    "hierarchical_id": r.get("hierarchical_id", ""),
                },
            })

        # Preserve PPR ranking: sort by PPR score descending.
        if scores:
            chunks_list.sort(key=lambda c: c.get("_ppr_score", 0.0), reverse=True)

        # Text-based dedup: when group_ids spans multiple groups with
        # overlapping content (e.g. own group + __global__ sharing the
        # same PDFs), PPR returns duplicate passages.  Keep the highest-
        # scored copy of each unique text to maximise evidence diversity.
        seen_texts: set[str] = set()
        deduped: list[dict] = []
        for chunk in chunks_list:
            txt_key = chunk.get("text", "").strip()[:200]
            if txt_key not in seen_texts:
                seen_texts.add(txt_key)
                deduped.append(chunk)
        if len(deduped) < len(chunks_list):
            logger.info(
                "route7_fetch_text_dedup",
                before=len(chunks_list),
                after=len(deduped),
                removed=len(chunks_list) - len(deduped),
            )
        chunks_list = deduped

        return chunks_list

    # ======================================================================
    # Phase 2: Structural Seeds (Tier 2)
    # ======================================================================

    async def _resolve_structural_seeds(
        self,
        query: str,
        folder_id: Optional[str] = None,
    ) -> Tuple[List[str], List[str]]:
        """Resolve structural seeds via section embedding matching.

        Reuses existing infrastructure from seed_resolver.py.

        Returns:
            Tuple of (entity_ids, section_titles).
        """
        try:
            from ..pipeline.seed_resolver import (
                match_sections_by_embedding,
                resolve_section_entities,
            )

            voyage_service = _get_voyage_service()
            if not voyage_service or not self._async_neo4j:
                return [], []

            # Match sections by embedding similarity
            matched_sections = await match_sections_by_embedding(
                async_neo4j=self._async_neo4j,
                query=query,
                group_id=self.group_id,
                embed_model=voyage_service,
                group_ids=self.group_ids,
            )

            if not matched_sections:
                return [], []

            # Expand matched sections to include child sections
            expanded_sections = list(matched_sections)
            if self.neo4j_driver:
                try:
                    def _expand_children():
                        with retry_session(self.neo4j_driver, read_only=True) as session:
                            records = session.run("""
                                UNWIND $paths AS parent_path
                                MATCH (parent:Section)
                                WHERE parent.group_id IN $group_ids
                                  AND parent.path_key = parent_path
                                MATCH (child:Section)-[:SUBSECTION_OF*1..3]->(parent)
                                WHERE child.group_id IN $group_ids
                                RETURN DISTINCT child.path_key AS child_path
                            """, paths=matched_sections, group_ids=self.group_ids)
                            return [r["child_path"] for r in records if r["child_path"]]
                    child_paths = await asyncio.to_thread(_expand_children)
                    expanded_sections.extend(child_paths)
                    expanded_sections = list(set(expanded_sections))
                    logger.debug(
                        "route7_child_section_expansion",
                        matched=len(matched_sections),
                        expanded=len(expanded_sections),
                    )
                except Exception as e:
                    logger.debug("route7_child_section_expansion_failed", error=str(e))

            # Resolve entities from expanded sections
            folder_id = folder_id if folder_id is not None else self.folder_id
            section_entities = await resolve_section_entities(
                async_neo4j=self._async_neo4j,
                section_paths=expanded_sections,
                group_id=self.group_id,
                folder_id=folder_id,
                group_ids=self.group_ids,
            )

            entity_ids = list({e["id"] for e in section_entities if e.get("id")})

            logger.info(
                "route7_structural_seeds",
                sections=len(matched_sections),
                entities=len(entity_ids),
            )
            return entity_ids, matched_sections

        except Exception as e:
            logger.warning("route7_structural_seeds_failed", error=str(e))
            return [], []

    # ======================================================================
    # Phase 2: Community Seeds (Tier 3)
    # ======================================================================

    async def _resolve_community_seeds(
        self,
        query: str,
        include_sentences: bool = False,
        *,
        adaptive_ratio: float | None = None,
        max_k: int | None = None,
        folder_id: Optional[str] = None,
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str], Dict[str, List[str]]]:
        """Resolve community seeds via community embedding matching.

        Returns:
            Tuple of (entity_ids, community_data, sentence_ids, per_community).
            sentence_ids is populated only when include_sentences=True.
            per_community maps community_id → [sentence_eid] (empty when
            include_sentences=False).
        """
        try:
            folder_id = folder_id if folder_id is not None else self.folder_id
            community_matcher = self.pipeline.community_matcher
            if not community_matcher or not self._async_neo4j:
                return [], [], [], {}

            # Match communities (returns list of (community_dict, score) tuples)
            matched_tuples = await community_matcher.match_communities(
                query, relative_threshold=adaptive_ratio, max_k=max_k,
                folder_id=folder_id,
            )
            if not matched_tuples:
                return [], [], [], {}

            matched = [t[0] for t in matched_tuples]
            # Resolve entities from matched communities
            community_ids = [c.get("id") for c in matched if c.get("id")]
            if not community_ids:
                return [], matched, [], {}

            cypher = """
            UNWIND $community_ids AS cid
            MATCH (e:Entity)-[:BELONGS_TO]->(c:Community {id: cid})
            WHERE c.group_id IN $group_ids AND e.group_id IN $group_ids
            RETURN e.id AS entity_id, e.name AS entity_name, c.id AS community_id
            ORDER BY e.degree DESC
            LIMIT 15
            """

            async with self._async_neo4j._get_session() as session:
                result = await session.run(
                    cypher,
                    community_ids=community_ids,
                    group_ids=self.group_ids,
                    folder_id=folder_id,
                )
                records = await result.data()

            entity_ids = list({r["entity_id"] for r in records if r.get("entity_id")})

            # Resolve sentence IDs via Community→Entity→Sentence traversal.
            # Return interleaved across communities so each community gets
            # fair representation even when downstream caps apply.
            sentence_ids: List[str] = []
            if include_sentences and community_ids:
                sent_cypher = """
                UNWIND $community_ids AS cid
                MATCH (e:Entity)-[:BELONGS_TO]->(c:Community {id: cid})
                WHERE e.group_id IN $group_ids
                MATCH (e)<-[:MENTIONS]-(s:Sentence)
                WHERE s.group_id IN $group_ids
                RETURN DISTINCT cid AS community_id, s.id AS sentence_eid
                """
                async with self._async_neo4j._get_session() as session:
                    sent_result = await session.run(
                        sent_cypher,
                        community_ids=community_ids,
                        group_ids=self.group_ids,
                        folder_id=folder_id,
                    )
                    sent_records = await sent_result.data()

                # Group by community, then round-robin interleave
                from collections import defaultdict
                per_community: Dict[str, List[str]] = defaultdict(list)
                for r in sent_records:
                    sid = r.get("sentence_eid")
                    cid = r.get("community_id")
                    if sid and cid:
                        per_community[cid].append(sid)

                seen: set = set()
                iterators = [iter(sids) for sids in per_community.values()]
                while iterators:
                    next_round = []
                    for it in iterators:
                        sid = next(it, None)
                        if sid is not None:
                            if sid not in seen:
                                sentence_ids.append(sid)
                                seen.add(sid)
                            next_round.append(it)
                    iterators = next_round

            logger.info(
                "route7_community_seeds",
                communities=len(matched),
                entities=len(entity_ids),
                sentences=len(sentence_ids),
            )
            return entity_ids, matched, sentence_ids, dict(per_community) if include_sentences else {}

        except Exception as e:
            logger.warning("route7_community_seeds_failed", error=str(e))
            return [], [], [], {}

    # ======================================================================
    # Phase 2: Sentence Vector Search (copied from Route 5 pattern)
    # ======================================================================

    async def _retrieve_sentence_evidence(
        self,
        query: str,
        top_k: int = 30,
        folder_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve sentence-level evidence via Voyage vector search.

        Uses the sentence_embedding Neo4j vector index —
        same pattern as Route 5.
        """
        voyage_service = _get_voyage_service()
        if not voyage_service or not self.neo4j_driver:
            return []

        try:
            query_embedding = await asyncio.to_thread(voyage_service.embed_query, query)
        except Exception as e:
            logger.warning("route7_sentence_embed_failed", error=str(e))
            return []

        threshold = float(os.getenv("ROUTE7_SENTENCE_THRESHOLD", "0.2"))
        group_ids = self.group_ids
        folder_id = folder_id if folder_id is not None else self.folder_id

        cypher = """CYPHER 25
        CALL () {
            MATCH (sent:Sentence)
            SEARCH sent IN (VECTOR INDEX sentence_embedding FOR $embedding WHERE sent.group_id = $group_id LIMIT $top_k)
            SCORE AS score
            WHERE score >= $threshold
            RETURN sent, score
            UNION ALL
            MATCH (sent:Sentence)
            SEARCH sent IN (VECTOR INDEX sentence_embedding FOR $embedding WHERE sent.group_id = $global_group_id LIMIT $top_k)
            SCORE AS score
            WHERE score >= $threshold
            RETURN sent, score
        }

        OPTIONAL MATCH (sent)-[:IN_DOCUMENT]->(doc:Document)
        WHERE doc.group_id IN $group_ids

        RETURN sent.id AS sentence_id,
               sent.text AS text,
               sent.source AS source,
               sent.section_path AS section_path,
               sent.hierarchical_id AS hierarchical_id,
               sent.page AS page,
               sent.parent_text AS chunk_text,
               doc.title AS document_title,
               doc.id AS document_id,
               doc.source AS document_source,
               score
        ORDER BY score DESC
        """

        try:
            driver = self.neo4j_driver

            def _run_search():
                with retry_session(driver, read_only=True) as session:
                    records = session.run(
                        cypher,
                        embedding=query_embedding,
                        group_id=self.group_id,
                        global_group_id=settings.GLOBAL_GROUP_ID,
                        group_ids=group_ids,
                        top_k=top_k,
                        threshold=threshold,
                        folder_id=folder_id,
                    )
                    return [dict(r) for r in records]

            results = await asyncio.to_thread(_run_search)
        except Exception as e:
            logger.warning("route7_sentence_search_failed", error=str(e))
            return []

        if not results:
            return []

        # Deduplicate
        seen: set = set()
        evidence: List[Dict[str, Any]] = []
        for r in results:
            sid = r.get("sentence_id", "")
            if sid in seen:
                continue
            seen.add(sid)
            evidence.append({
                "text": r.get("text", "").strip(),
                "score": r.get("score", 0),
                "document_title": r.get("document_title", "Unknown"),
                "document_id": r.get("document_id", ""),
                "document_source": r.get("document_source", ""),
                "section_path": r.get("section_path", ""),
                "hierarchical_id": r.get("hierarchical_id", ""),
                "page": r.get("page"),
                "sentence_id": sid,
            })

        logger.debug(
            "route7_sentence_search_complete",
            raw=len(results),
            deduped=len(evidence),
        )
        return evidence

    # ==================================================================
    # Step 4.7 helper: Cross-encoder reranking (legacy — kept as fallback)
    # ==================================================================

    async def _rerank_passages(
        self,
        query: str,
        candidate_ids: List[str],
        top_k: int = 20,
        relevance_threshold: float = 0.0,
        dynamic_max: int = 0,
        user_id: Optional[str] = None,
    ) -> List[Tuple[str, float]]:
        """Rerank candidate sentence IDs using voyage-rerank-2.5.

        Fetches sentence text from Neo4j, calls the Voyage cross-encoder,
        and returns reranked sentence IDs with relevance scores (best first).

        When relevance_threshold > 0, uses dynamic cutoff: keeps all passages
        above the threshold instead of a fixed top-K.  dynamic_max caps
        the total to avoid context overflow.

        Args:
            query: The user query.
            candidate_ids: Sentence node IDs to rerank.
            top_k: Max passages to return (used when threshold is 0).
            relevance_threshold: Min relevance_score to keep (0 = disabled).
            dynamic_max: Hard cap when using dynamic cutoff (0 = top_k).

        Returns:
            Reranked list of (sentence_id, relevance_score) tuples.
        """
        rerank_model = os.getenv("ROUTE7_RERANK_MODEL", "rerank-2.5")

        # Fetch sentence texts from Neo4j
        if not self.neo4j_driver:
            return [(cid, 1.0 - i * 0.01) for i, cid in enumerate(candidate_ids[:top_k])]

        group_ids = self.group_ids

        def _fetch_texts():
            with retry_session(self.neo4j_driver, read_only=True) as session:
                result = session.run(
                    "UNWIND $ids AS sid "
                    "MATCH (s:Sentence {id: sid}) "
                    "WHERE s.group_id IN $group_ids "
                    "RETURN s.id AS id, s.text AS text",
                    ids=candidate_ids,
                    group_ids=group_ids,
                )
                return {r["id"]: r["text"] or "" for r in result}

        text_map = await asyncio.to_thread(_fetch_texts)

        # Build ordered document list (preserve candidate order for fallback)
        documents = []
        valid_ids = []
        for cid in candidate_ids:
            text = text_map.get(cid, "")
            if text:
                documents.append(text)
                valid_ids.append(cid)

        if not documents:
            return [(cid, 1.0 - i * 0.01) for i, cid in enumerate(candidate_ids[:top_k])]

        # When dynamic cutoff is active, request ALL candidates from Voyage so
        # low-scoring passages are visible for threshold filtering.  Without
        # this, Voyage only returns top-K which all score high, making the
        # threshold useless.
        if relevance_threshold > 0:
            request_k = len(documents)
        else:
            request_k = min(top_k, len(documents))

        # Call Voyage reranker
        vc = make_voyage_client()

        rr_result = await rerank_with_retry(
            vc, query=query, documents=documents,
            model=rerank_model, top_k=request_k,
        )

        # Apply dynamic relevance cutoff or fixed top-K
        if relevance_threshold > 0:
            scored = [
                (valid_ids[rr.index], rr.relevance_score)
                for rr in rr_result.results
                if rr.relevance_score >= relevance_threshold
            ]
            if dynamic_max > 0:
                scored = scored[:dynamic_max]
        else:
            scored = [
                (valid_ids[rr.index], rr.relevance_score)
                for rr in rr_result.results
            ]

        # Track reranker usage (fire-and-forget)
        try:
            _rerank_tokens = getattr(rr_result, "total_tokens", 0)
            acc = getattr(self, "_token_accumulator", None)
            if acc is not None:
                acc.add_rerank(rerank_model, _rerank_tokens, len(documents))
            from src.core.services.usage_tracker import get_usage_tracker
            _tracker = get_usage_tracker()
            asyncio.ensure_future(_tracker.log_rerank_usage(
                partition_id=user_id if user_id else self.group_id,
                model=rerank_model,
                total_tokens=_rerank_tokens,
                documents_reranked=len(documents),
                route="route_7",
                user_id=user_id,
            ))
        except Exception:
            pass

        # Log ALL scores from Voyage (before threshold filter) for diagnosis
        all_scores_desc = sorted(
            [(valid_ids[rr.index], round(rr.relevance_score, 4)) for rr in rr_result.results],
            key=lambda x: -x[1],
        )

        min_score = round(scored[-1][1], 4) if scored else 0
        logger.info(
            "route7_rerank_complete",
            model=rerank_model,
            input=len(documents),
            output=len(scored),
            ids_without_text=len(candidate_ids) - len(valid_ids),
            top_score=round(scored[0][1], 4) if scored else 0,
            min_score=min_score,
            threshold=relevance_threshold,
            dynamic=relevance_threshold > 0,
            all_scores=[s for _, s in all_scores_desc],
        )

        # DEBUG: dump kept vs dropped with texts for pipeline analysis
        scored_ids = {sid for sid, _ in scored}
        dropped_with_text = [
            {"id": sid, "score": sc, "text": text_map.get(sid, "")[:200]}
            for sid, sc in all_scores_desc if sid not in scored_ids
        ]
        if dropped_with_text:
            logger.info(
                "debug_reranker_dropped",
                count=len(dropped_with_text),
                items=dropped_with_text,
            )

        return scored

    # ==================================================================
    # Step 4.4 helper: Semantic pre-filter via embedding similarity
    # ==================================================================

    async def _semantic_prefilter_passages(
        self,
        query: str,
        candidate_ids: List[str],
        top_n: int = 30,
    ) -> List[str]:
        """Pre-filter PPR candidates by instructed embedding similarity.

        Fast path: if PPR engine has cached passage embeddings, computes
        cosine similarity in-memory (no Neo4j roundtrip).

        Slow path: falls back to Neo4j vector.similarity.cosine() query.
        """
        # Fast path: in-memory cosine using cached PPR embeddings
        if self._ppr_engine and self._ppr_engine.get_all_passage_embeddings():
            voyage_service = _get_voyage_service()
            if voyage_service:
                instruction = os.getenv(
                    "ROUTE7_SEMANTIC_PREFILTER_INSTRUCTION",
                    "Retrieve all sentences relevant to answering the following query.",
                )
                try:
                    instructed_query = instruction + " " + query
                    query_embedding = await asyncio.to_thread(
                        voyage_service.embed_query, instructed_query,
                    )
                    prefiltered = self._ppr_engine.cosine_prefilter(
                        query_embedding, top_k=top_n, candidate_ids=candidate_ids,
                    )
                    if prefiltered:
                        return [sid for sid, _ in prefiltered]
                except Exception as e:
                    logger.warning("prefilter_inmemory_failed_fallback", error=str(e))

        # Slow path: Neo4j-based cosine similarity
        voyage_service = _get_voyage_service()
        if not voyage_service or not self.neo4j_driver:
            return candidate_ids[:top_n]

        instruction = os.getenv(
            "ROUTE7_SEMANTIC_PREFILTER_INSTRUCTION",
            "Retrieve all sentences relevant to answering the following query.",
        )
        try:
            instructed_query = instruction + " " + query
            query_embedding = await asyncio.to_thread(voyage_service.embed_query, instructed_query)
        except Exception as e:
            logger.warning("prefilter_embed_failed", error=str(e))
            return candidate_ids[:top_n]

        group_ids = self.group_ids
        driver = self.neo4j_driver

        def _compute_similarities():
            with retry_session(driver, read_only=True) as session:
                result = session.run(
                    "UNWIND $ids AS sid "
                    "MATCH (s:Sentence {id: sid}) "
                    "WHERE s.group_id IN $group_ids "
                    "  AND s.sentence_embedding IS NOT NULL "
                    "RETURN s.id AS id, "
                    "  vector.similarity.cosine(s.sentence_embedding, $qemb) AS sim",
                    ids=candidate_ids,
                    group_ids=group_ids,
                    qemb=query_embedding,
                )
                return [(r["id"], r["sim"]) for r in result]

        sim_results = await asyncio.to_thread(_compute_similarities)
        sim_results.sort(key=lambda x: -x[1])
        return [sid for sid, _ in sim_results[:top_n]]

    # ==================================================================
    # Step 2 helper: Rerank ALL sentences using PPR-cached texts (legacy)
    # ==================================================================

    async def _rerank_all_passages(
        self,
        query: str,
        top_k: int = 20,
        relevance_threshold: float = 0.0,
        dynamic_max: int = 0,
        user_id: Optional[str] = None,
        prefilter_top_k: int = 0,
    ) -> List[Tuple[str, float]]:
        """Rerank sentences using cached texts from the PPR engine.

        Two-stage pipeline to reduce cross-encoder token usage:
        1. If prefilter_top_k > 0 and passage embeddings are cached, uses
           fast in-memory cosine similarity to narrow ALL passages down to
           the top prefilter_top_k candidates.
        2. Cross-encoder (voyage rerank-2.5) reranks only the pre-filtered
           candidates for final scoring.

        Without pre-filtering (prefilter_top_k=0), reranks ALL passages
        directly (original behavior).

        When relevance_threshold > 0, returns all passages above threshold
        (up to dynamic_max) instead of a fixed top-K.

        Returns list of (sentence_id, relevance_score) sorted best-first.
        """
        rerank_model = os.getenv("ROUTE7_RERANK_MODEL", "rerank-2.5")

        text_map = self._ppr_engine.get_all_passage_texts()
        if not text_map:
            logger.warning("rerank_all_no_texts")
            return []

        # Stage 1: Embedding pre-filter (optional)
        prefiltered_ids: Optional[set] = None
        if prefilter_top_k > 0 and self._ppr_engine.get_all_passage_embeddings():
            from ..embeddings.voyage_embed import get_voyage_embed_service
            try:
                voyage_svc = get_voyage_embed_service()
                # Instructed embedding steers cosine toward retrieval intent
                instruction = os.getenv(
                    "ROUTE7_RERANK_PREFILTER_INSTRUCTION",
                    "Retrieve all document passages relevant to answering this query: ",
                )
                instructed_query = f"{instruction}{query}" if instruction else query
                q_emb = voyage_svc.embed_query(
                    instructed_query, group_id=self.group_id, user_id=user_id,
                )
                prefiltered = self._ppr_engine.cosine_prefilter(
                    q_emb, top_k=prefilter_top_k,
                )
                prefiltered_ids = {sid for sid, _ in prefiltered}
                logger.info(
                    "rerank_all_prefilter_applied",
                    total_passages=len(text_map),
                    prefilter_top_k=prefilter_top_k,
                    prefiltered=len(prefiltered_ids),
                )
            except Exception as e:
                logger.warning("rerank_all_prefilter_failed", error=str(e))
                # Fall through to rerank all

        ids = []
        documents = []
        for sid, text in text_map.items():
            if not text.strip():
                continue
            if prefiltered_ids is not None and sid not in prefiltered_ids:
                continue
            ids.append(sid)
            documents.append(text)

        if not documents:
            return []

        effective_k = max(top_k, dynamic_max) if dynamic_max > 0 else top_k
        request_k = min(effective_k, len(documents))

        vc = make_voyage_client()

        rr_result = await rerank_with_retry(
            vc, query=query, documents=documents,
            model=rerank_model, top_k=request_k,
        )

        # Apply dynamic relevance cutoff or return all
        if relevance_threshold > 0:
            results = [
                (ids[rr.index], rr.relevance_score)
                for rr in rr_result.results
                if rr.relevance_score >= relevance_threshold
            ]
        else:
            results = [
                (ids[rr.index], rr.relevance_score)
                for rr in rr_result.results
            ]

        # Track reranker usage (fire-and-forget)
        try:
            _rerank_tokens = getattr(rr_result, "total_tokens", 0)
            acc = getattr(self, "_token_accumulator", None)
            if acc is not None:
                acc.add_rerank(rerank_model, _rerank_tokens, len(documents))
            from src.core.services.usage_tracker import get_usage_tracker
            _tracker = get_usage_tracker()
            asyncio.ensure_future(_tracker.log_rerank_usage(
                partition_id=user_id if user_id else self.group_id,
                model=rerank_model,
                total_tokens=_rerank_tokens,
                documents_reranked=len(documents),
                route="route_7",
                user_id=user_id,
            ))
        except Exception:
            pass

        min_score = round(results[-1][1], 4) if results else 0
        logger.info(
            "route7_rerank_all_complete",
            model=rerank_model,
            input=len(documents),
            output=len(results),
            top_score=round(results[0][1], 4) if results else 0,
            min_score=min_score,
            threshold=relevance_threshold,
            dynamic=relevance_threshold > 0,
            prefiltered=prefiltered_ids is not None,
        )

        return results

    # ------------------------------------------------------------------
    # Step 4.7 helper: LLM relevance filter
    # ------------------------------------------------------------------
    async def _llm_relevance_filter(
        self,
        query: str,
        candidate_passages: List[Tuple[str, float]],
        text_map: Dict[str, str],
    ) -> Optional[List[Tuple[str, float]]]:
        """Filter passages through an LLM that judges relevance to the query.

        Sends all candidate passages in a single batch prompt, asking the LLM
        to return the indices of passages that are directly relevant.
        Returns filtered list preserving original scores, or None on failure.
        """
        if not candidate_passages:
            return candidate_passages

        # Build numbered passage list for the prompt
        passage_lines = []
        id_index = []
        for i, (cid, score) in enumerate(candidate_passages):
            text = text_map.get(cid, "").strip()
            if not text:
                continue
            passage_lines.append(f"[{i}] {text}")
            id_index.append((i, cid, score))

        if not passage_lines:
            return candidate_passages

        filter_model = os.getenv("ROUTE7_LLM_FILTER_MODEL", "gpt-4.1-mini")

        system_prompt = (
            "You are a precision relevance filter for a document QA system. "
            "Given a user question and a numbered list of text passages, "
            "return ONLY the indices of passages that contain information "
            "DIRECTLY relevant to answering the specific question asked. "
            "Exclude passages that are merely tangentially related or from "
            "the same domain but about a different topic.\n\n"
            "Return a JSON array of integers, e.g. [0, 3, 7, 12]. "
            "If no passages are relevant, return []. "
            "Return ONLY the JSON array, no other text."
        )

        user_prompt = (
            f"Question: {query}\n\n"
            f"Passages:\n" + "\n".join(passage_lines)
        )

        # Get LLM client
        from src.worker.services.llm_service import LLMService
        llm_svc = LLMService()
        llm_client = llm_svc._create_llm_client(filter_model)

        response = await llm_client.acomplete(
            system_prompt + "\n\n" + user_prompt
        )
        text = response.text.strip()

        # Parse JSON array from response
        match = re.search(r'\[[\d,\s]*\]', text)
        if not match:
            logger.warning("llm_filter_no_json", raw=text[:200])
            return None

        kept_indices = set(json.loads(match.group()))

        # Map indices back to (cid, score) tuples
        filtered = [
            (cid, score) for idx, cid, score in id_index
            if idx in kept_indices
        ]

        logger.info(
            "llm_filter_complete",
            model=filter_model,
            input=len(id_index),
            kept=len(filtered),
            removed=len(id_index) - len(filtered),
        )

        return filtered

    # ==================================================================
    # Per-document map-reduce synthesis
    # ==================================================================

    _MAP_EXTRACT_PROMPT = """You are a precise fact extractor. Your job is to find ALL information in this document that could be relevant to answering the question below.

Question: {query}

Document: {doc_title}
Content:
{content}

Instructions:
- Cast a WIDE net: extract any fact, detail, provision, data point, relationship, or reference that relates to the question — even tangentially.
- Think about SYNONYMS and RELATED CONCEPTS: the question may use different terminology than the document. If the document discusses the same topic using different words, extract it. Think broadly about the question's topic and include provisions that fall under the same conceptual umbrella, even if the exact wording differs.
- Include exact numeric values, dates, names, amounts, and conditions VERBATIM.
- Extract EACH distinct provision, condition, or requirement as a SEPARATE fact — do not merge multiple provisions into one fact.
- Even single-sentence mentions count — do NOT skip brief references.
- When in doubt, INCLUDE the fact. Over-extraction is better than missing relevant content.
- Return a JSON array of objects. Each object has:
  "fact": a concise statement of the extracted fact,
  "quote": the exact text from the document supporting this fact.
- If this document contains truly NO relevant information, return an empty array: []

Return ONLY valid JSON — no markdown fences, no commentary:"""

    _REDUCE_MERGE_PROMPT = """You are an expert analyst. Merge these per-document extractions into a final answer.

Question: {query}

Extracted facts from {n_docs} documents:
{facts_block}

Instructions:
1. REFUSAL CHECK — apply this for SPECIFIC LOOKUP questions:
   - If the question asks for a SINGLE specific data point, term, clause, or identifier:
     a. Identify the KEY TERM in the question (e.g., "mold damage", "routing number", "IBAN").
     b. Check if ANY extracted fact DIRECTLY and EXPLICITLY addresses that key term.
     c. If NO fact explicitly addresses it, respond ONLY with: "The requested information was not found in the available documents."
     d. Do NOT infer or generalize. "Environmental pollutants" is NOT a match for "mold damage." A clause that COULD THEORETICALLY apply to the key term is NOT a match — the key term must be explicitly named.
     e. If facts only describe general exclusions, disclaimers, or related topics WITHOUT naming the exact key term from the question, that is NOT a match — REFUSE.
   - This refusal does NOT apply to questions that ask to "summarize", "list", "compare", or "identify" across documents — those are enumeration questions and should always be answered from the extracted facts.
2. SCOPE FILTER — read the question carefully and identify its SPECIFIC TOPIC:
   - ONLY include facts that DIRECTLY answer or fall within the question's requested scope/category.
   - DISCARD facts about other topics, even if they were extracted from the same document.
   - Example: if the question asks about "reporting obligations," do NOT include insurance requirements, payment terms, or contact details.
   - Example: if the question asks about "named parties/organizations," do NOT include jurisdictions, statutes, or non-organization entities.
   - When a question uses a term with multiple senses (e.g., "forfeiture"), stay within the question's context. Financial/payment forfeiture ≠ procedural loss of legal rights; product warranty ≠ service warranty.
   - Raw contact details (phone numbers, fax, email addresses) are NOT "notice/delivery mechanisms" — only include them if they are part of a contractual notice REQUIREMENT.
3. Deduplicate: if multiple documents state the same fact, keep ONE bullet citing all source documents.
4. One bullet per UNIQUE item — do not repeat or paraphrase the same fact.
5. Include the exact values from the extractions (numbers, timeframes, names).
6. Cite document sources in parentheses, e.g. (Source: Document Title).
7. Be CONCISE — state each fact once, move on. Do not add commentary or explanation.
8. RESPECT ALL QUALIFIERS from the question.
9. Include facts that address the question's topic using DIFFERENT TERMINOLOGY — but only if they truly answer the question, not merely because they come from a relevant document.
10. COVERAGE: Every document that has relevant extracted facts MUST appear in your response. Do not skip documents.

Respond using ONLY bullet points — no headers, no preamble, no summary paragraph:

- [Fact (Source: Document)]
- [Fact (Source: Document)]

Response:"""

    async def _map_reduce_synthesize(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        evidence_nodes: List[Tuple[str, float]],
        prompt_variant: Optional[str] = None,
        synthesis_model: Optional[str] = None,
        include_context: bool = False,
        language: Optional[str] = None,
        max_tokens: Optional[int] = None,
        concurrency: int = 8,
        graph_structural_header: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Per-document extraction → merge synthesis.

        MAP:  For each document's chunks, ask LLM to extract relevant facts.
              Each doc has ≤5 chunks so LLM cannot miss anything.
        REDUCE: Merge all per-doc extractions, deduplicate, format answer.
        """
        # ── Group chunks by document ─────────────────────────────────
        doc_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        doc_titles: Dict[str, str] = {}
        for chunk in chunks:
            meta = chunk.get("metadata", {}) or {}
            doc_id = (
                meta.get("document_id")
                or chunk.get("document_id")
                or chunk.get("source", "unknown")
            )
            if "_sent_" in str(chunk.get("chunk_id", "")):
                doc_id = str(chunk["chunk_id"]).split("_sent_")[0]
            doc_groups[doc_id].append(chunk)
            if doc_id not in doc_titles:
                doc_titles[doc_id] = (
                    meta.get("document_title")
                    or chunk.get("document_title")
                    or chunk.get("source")
                    or doc_id
                )

        logger.info(
            "map_reduce_grouping",
            total_chunks=len(chunks),
            num_documents=len(doc_groups),
            doc_chunk_counts={did: len(chs) for did, chs in doc_groups.items()},
        )

        # ── Resolve LLM client ──────────────────────────────────────
        llm = self.pipeline.synthesizer.llm
        if synthesis_model:
            try:
                from src.worker.services.llm_service import LLMService
                llm = LLMService()._create_llm_client(synthesis_model)
                if hasattr(self.pipeline.synthesizer.llm, "_accumulator") and hasattr(llm, "set_accumulator"):
                    llm.set_accumulator(
                        object.__getattribute__(self.pipeline.synthesizer.llm, "_accumulator")
                    )
                    for attr in ("_group_id", "_user_id", "_route"):
                        try:
                            object.__setattr__(
                                llm, attr,
                                object.__getattribute__(self.pipeline.synthesizer.llm, attr),
                            )
                        except AttributeError:
                            pass
            except Exception as e:
                logger.warning("map_reduce_model_override_failed", error=str(e))
                llm = self.pipeline.synthesizer.llm

        # ── MAP phase: parallel per-doc extraction ───────────────────
        semaphore = asyncio.Semaphore(concurrency)
        quote_overlap_threshold = 0.5  # configurable: discard facts below this

        # Precompute key-phrase set for hallucination guard (shared by
        # _extract_one and _retry_extract).
        _stopwords = {"the", "and", "for", "are", "but", "not", "you",
                      "all", "can", "her", "was", "one", "our", "out",
                      "what", "which", "their", "from", "have", "has",
                      "this", "that", "with", "they", "been", "how",
                      "about", "across", "documents", "document", "list",
                      "summarize", "identify", "describe", "explain",
                      "named", "parties", "organizations", "mentioned",
                      "company", "companies", "clauses", "terms",
                      "explicit", "specific"}
        _query_lower = query.lower()
        _key_phrases = set(
            m.group(1).lower()
            for m in re.finditer(r'\*\*([^*]+)\*\*', query)
        )
        if not _key_phrases:
            _key_phrases = {
                w for w in re.findall(r'[a-z]+', _query_lower)
                if len(w) >= 6 and w not in _stopwords
            }

        async def _extract_one(doc_id: str, doc_chunks: List[Dict]) -> Dict:
            doc_title = doc_titles.get(doc_id, doc_id)
            content_parts = []
            for i, ch in enumerate(doc_chunks):
                text = ch.get("text") or ch.get("sentence_text", "")
                content_parts.append(f"[Passage {i+1}] {text}")
            content = "\n\n".join(content_parts)

            prompt = self._MAP_EXTRACT_PROMPT.format(
                query=query, doc_title=doc_title, content=content,
            )
            if language:
                prompt += f"\n\nExtract facts in {language}."

            async with semaphore:
                try:
                    resp = await acomplete_with_retry(llm, prompt, temperature=0)
                    raw = resp.text.strip()
                    # Parse JSON array
                    json_match = re.search(r'\[.*\]', raw, re.DOTALL)
                    if json_match:
                        facts = json.loads(json_match.group())
                        if not isinstance(facts, list):
                            facts = []
                    else:
                        facts = []
                except Exception as e:
                    logger.warning(
                        "map_extract_failed",
                        doc_id=doc_id, error=str(e),
                    )
                    facts = []

            # Validate: discard facts whose quote is fabricated (not in source)
            content_lower = content.lower()
            # _key_phrases and _stopwords are computed once above both closures
            validated = []
            for f in facts:
                if not isinstance(f, dict) or not f.get("fact"):
                    continue
                quote = (f.get("quote") or "").strip()
                if quote:
                    # Check word overlap between quote and source content
                    q_words = set(re.findall(r'[a-z0-9]+', quote.lower()))
                    c_words = set(re.findall(r'[a-z0-9]+', content_lower))
                    if q_words and len(q_words & c_words) / len(q_words) < quote_overlap_threshold:
                        logger.debug(
                            "map_fact_quote_mismatch",
                            doc_id=doc_id,
                            fact=f["fact"][:100],
                            quote_overlap=len(q_words & c_words) / len(q_words),
                        )
                        continue
                # Key-phrase hallucination check: if the fact echoes a
                # distinctive query phrase that doesn't exist in the source
                # content, the LLM likely injected it from the question.
                if _key_phrases:
                    fact_lower = f["fact"].lower()
                    hallucinated = False
                    for kp in _key_phrases:
                        # Check the full phrase
                        if kp in fact_lower and kp not in content_lower:
                            hallucinated = True
                        # For multi-word phrases, also check each distinctive
                        # word (4+ chars) — LLM may inject just part of the
                        # phrase (e.g., "mold" from "mold damage").
                        if not hallucinated and " " in kp:
                            for w in kp.split():
                                if len(w) >= 4 and w not in _stopwords:
                                    if w in fact_lower and w not in content_lower:
                                        hallucinated = True
                                        break
                        if hallucinated:
                            logger.debug(
                                "map_fact_keyphrase_hallucination",
                                doc_id=doc_id,
                                fact=f["fact"][:100],
                                hallucinated_phrase=kp,
                            )
                            break
                    if hallucinated:
                        continue
                validated.append(f)
            facts = validated

            return {
                "doc_id": doc_id,
                "doc_title": doc_title,
                "facts": facts,
                "num_chunks": len(doc_chunks),
                "chunks": doc_chunks,
            }

        map_tasks = [
            _extract_one(did, chs) for did, chs in doc_groups.items()
        ]
        map_results = await asyncio.gather(*map_tasks)

        # Collect all facts with document attribution
        all_facts_raw: List[Dict[str, Any]] = []
        total_extracted = 0
        for mr in map_results:
            for fact in mr["facts"]:
                if isinstance(fact, dict) and fact.get("fact"):
                    fact["_doc_title"] = mr["doc_title"]
                    fact["_doc_id"] = mr["doc_id"]
                    all_facts_raw.append(fact)
                    total_extracted += 1

        logger.info(
            "map_reduce_map_complete",
            num_documents=len(map_results),
            total_facts_extracted=total_extracted,
            facts_per_doc={mr["doc_title"][:40]: len(mr["facts"]) for mr in map_results},
        )

        # ── Dedup + cap facts per document title ─────────────────────
        # Duplicate doc copies (same title, different IDs) produce
        # redundant facts that overwhelm the REDUCE step.
        # Cap keeps the most query-relevant facts (by keyword overlap).
        max_facts_per_doc = 15
        title_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for fact in all_facts_raw:
            title_groups[fact["_doc_title"]].append(fact)

        # Build query keywords for relevance ranking (using prefix
        # matching so "disputes" ≈ "dispute", "remedies" ≈ "remedy")
        _q_words_raw = set(
            w for w in re.findall(r'[a-z]{3,}', query.lower())
        ) - {"the", "and", "for", "are", "all", "what", "which",
             "from", "this", "that", "with", "how", "across",
             "documents", "document", "list", "summarize", "describe"}
        # Use 5-char prefixes for fuzzy matching across morphological variants
        _PREFIX_LEN = 5
        _q_prefixes = set(w[:_PREFIX_LEN] for w in _q_words_raw if len(w) >= _PREFIX_LEN)

        def _prefix_overlap(fact_text: str) -> int:
            """Count how many query prefixes match any word in the fact."""
            f_words = set(re.findall(r'[a-z]{3,}', fact_text.lower()))
            f_prefixes = set(w[:_PREFIX_LEN] for w in f_words if len(w) >= _PREFIX_LEN)
            return len(f_prefixes & _q_prefixes)

        all_facts: List[Dict[str, Any]] = []
        all_overflow: List[Dict[str, Any]] = []
        for title, facts_list in title_groups.items():
            seen_keys: set = set()
            unique_facts: List[Dict[str, Any]] = []
            for f in facts_list:
                key = f["fact"].lower().strip()[:60]
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                unique_facts.append(f)
            if len(unique_facts) > max_facts_per_doc:
                # Rank by prefix overlap with query before capping
                for f in unique_facts:
                    f["_relevance"] = _prefix_overlap(f["fact"])
                unique_facts.sort(key=lambda f: -f.get("_relevance", 0))
                capped = unique_facts[:max_facts_per_doc]
                dropped = unique_facts[max_facts_per_doc:]
                logger.info(
                    "map_reduce_facts_capped",
                    doc_title=title[:40],
                    original=len(facts_list),
                    unique=len(unique_facts),
                    capped=len(capped),
                )
            else:
                capped = unique_facts
                dropped = []
            all_facts.extend(capped)
            all_overflow.extend(dropped)
        if len(all_facts) < total_extracted:
            logger.info(
                "map_reduce_dedup_summary",
                before=total_extracted,
                after=len(all_facts),
                per_doc={t[:40]: len([f for f in all_facts if f["_doc_title"] == t])
                         for t in title_groups},
            )

        # ── REDUCE phase: merge + deduplicate ────────────────────────
        if not all_facts:
            return {
                "response": "The requested information was not found in the available documents.",
                "citations": [],
                "evidence_path": [node for node, _ in evidence_nodes],
                "text_chunks_used": len(chunks),
                "sub_questions_addressed": [],
                "llm_context": None,
                "context_stats": {"map_reduce": True, "docs": len(doc_groups), "facts": 0},
                "sentence_citation_map": {},
            }

        # Build facts block for reduce prompt
        facts_lines = []
        for i, fact in enumerate(all_facts, 1):
            line = f'{i}. [{fact["_doc_title"]}] {fact["fact"]}'
            quote = fact.get("quote", "")
            if quote:
                line += f' (Quote: "{quote[:150]}")'
            facts_lines.append(line)
        facts_block = "\n".join(facts_lines)

        # Append overflow facts as supplementary context
        if all_overflow:
            overflow_lines = []
            for i, fact in enumerate(all_overflow, 1):
                overflow_lines.append(
                    f'{i}. [{fact["_doc_title"]}] {fact["fact"]}'
                )
            facts_block += (
                "\n\n--- ADDITIONAL EXTRACTED FACTS (lower priority, "
                "include if they add unique information not covered above) ---\n"
                + "\n".join(overflow_lines)
            )
            logger.info(
                "map_reduce_overflow_appended",
                overflow_count=len(all_overflow),
            )

        reduce_prompt = self._REDUCE_MERGE_PROMPT.format(
            query=query,
            n_docs=len(doc_groups),
            facts_block=facts_block,
        )
        # Append entity-document map from knowledge graph (covers entities
        # that may not appear in any chunk text, e.g. header-only mentions)
        if graph_structural_header:
            reduce_prompt += (
                "\n\n--- ENTITY-DOCUMENT MAP (from knowledge graph) ---\n"
                + graph_structural_header
                + "\n\nUse the entity-document map above to supplement "
                "your answer with any entities/parties not already covered "
                "by the extracted facts."
            )
        if language:
            reduce_prompt += f"\n\nIMPORTANT: Respond entirely in {language}."

        try:
            acomplete_kwargs: Dict[str, Any] = {"temperature": 0}
            if max_tokens is not None:
                acomplete_kwargs["max_tokens"] = max_tokens
            reduce_resp = await acomplete_with_retry(llm, reduce_prompt, **acomplete_kwargs)
            response = reduce_resp.text.strip()
        except Exception as e:
            logger.error("map_reduce_reduce_failed", error=str(e))
            # Fallback: concatenate map extractions as bullet points
            response = "\n".join(
                f"- [{f['_doc_title']}] {f['fact']}" for f in all_facts
            )

        logger.info(
            "map_reduce_reduce_complete",
            response_length=len(response),
            total_facts=len(all_facts),
        )

        # ── Build citations from original chunks ─────────────────────
        # Map facts back to their source document chunks for citation
        citations = []
        cite_idx = 1
        seen_doc_ids = set()
        for mr in map_results:
            if not mr["facts"]:
                continue
            if mr["doc_id"] in seen_doc_ids:
                continue
            seen_doc_ids.add(mr["doc_id"])
            for ch in mr["chunks"]:
                meta = ch.get("metadata", {}) or {}
                citations.append({
                    "citation": f"[{cite_idx}]",
                    "citation_type": "chunk",
                    "chunk_id": ch.get("chunk_id", f"chunk_{cite_idx}"),
                    "document_id": mr["doc_id"],
                    "document_title": mr["doc_title"],
                    "document_url": meta.get("url", ""),
                    "text": ch.get("text", ch.get("sentence_text", "")),
                    "text_preview": (ch.get("text") or ch.get("sentence_text", ""))[:200],
                    "page_number": ch.get("page") or meta.get("page_number"),
                    "section_path": meta.get("section_path", ""),
                    "score": ch.get("_entity_score", 0.0),
                    "source": "map_reduce",
                })
                cite_idx += 1

        context_for_debug = None
        if include_context:
            context_for_debug = (
                f"=== MAP-REDUCE SYNTHESIS ===\n"
                f"Documents: {len(doc_groups)}\n"
                f"Total facts extracted: {total_extracted}\n\n"
                f"--- MAP EXTRACTIONS ---\n{facts_block}\n\n"
                f"--- REDUCE PROMPT ---\n{reduce_prompt}"
            )

        return {
            "response": response,
            "citations": citations,
            "evidence_path": [node for node, _ in evidence_nodes],
            "text_chunks_used": len(chunks),
            "sub_questions_addressed": [],
            "llm_context": context_for_debug,
            "context_stats": {
                "map_reduce": True,
                "num_documents": len(doc_groups),
                "total_facts": total_extracted,
            },
            "sentence_citation_map": {},
        }
