"""Route 6: Concept Search — Community-Aware Synthesis.

Best for thematic/cross-document concept queries:
- "What are the main compliance risks?"
- "Summarize key themes across documents"
- "Compare termination clauses across agreements"

Architecture (3 steps, 1 LLM call):
  1. Community Match + Sentence Search + Section Heading Search  (parallel)
  1b. Entity-centric sentence expansion via shared MENTIONS edges (R6-XII)
  2. Denoise + Rerank sentence evidence
  3. Synthesize community summaries + section headings + sentence evidence (single LLM call)

Key difference from Route 3 (MAP-REDUCE):
- No MAP phase: community summaries are passed directly to synthesis
- 1 LLM call total instead of N+1
- Community summaries provide thematic framing, not extracted claims
- Section headings provide document structure (via structural_embedding)
- Validated by benchmarks: MAP adds +41% latency for +1% containment

Design rationale:
  ANALYSIS_ROUTE3_LAZYGRAPHRAG_DEVIATION_AND_ROUTE6_PLAN_2026-02-19.md
"""

import asyncio
import json
import os
import re
import time
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import structlog
import tiktoken

from src.core.config import settings
from .base import BaseRouteHandler, Citation, RouteResult, rerank_with_retry, make_voyage_client, acomplete_with_retry
from .route_6_prompts import (
    CONCEPT_SYNTHESIS_PROMPT,
    COMMUNITY_EXTRACT_PROMPT,
    SYNTHESIS_COMPLETENESS_CHECK_PROMPT,
    COMMUNITY_MAP_SYNTHESIS_PROMPT,
    REDUCE_SYNTHESIS_PROMPT,
)
from ..services.neo4j_retry import retry_session

# Shared tiktoken encoder for token budget control (Feature 4)
_tiktoken_enc = tiktoken.get_encoding("cl100k_base")

logger = structlog.get_logger(__name__)

# Voyage embedding service (lazy singleton) — shared with Route 3
_voyage_service = None
_voyage_init_attempted = False
_voyage_init_lock = threading.Lock()


def _get_voyage_service():
    """Get Voyage embedding service for sentence search."""
    global _voyage_service, _voyage_init_attempted
    if _voyage_init_attempted:
        return _voyage_service
    with _voyage_init_lock:
        if not _voyage_init_attempted:
            _voyage_init_attempted = True
            try:
                from src.core.config import settings
                if settings.VOYAGE_API_KEY:
                    from src.worker.hybrid_v2.embeddings.voyage_embed import VoyageEmbedService
                    _voyage_service = VoyageEmbedService()
                    logger.info("route6_voyage_service_initialized")
                else:
                    logger.warning("route6_voyage_service_no_api_key")
            except Exception as e:
                logger.warning("route6_voyage_service_init_failed", error=str(e))
    return _voyage_service


class ConceptSearchHandler(BaseRouteHandler):
    """Route 6: Community-aware concept search with direct synthesis.

    Restores the LazyGraphRAG insight (community summaries as thematic
    context) while keeping Route 3's proven sentence search.  Eliminates
    the MAP phase that added latency without proportional accuracy gain.
    """

    ROUTE_NAME = "route_6_concept_search"

    async def execute(
        self,
        query: str,
        response_type: str = "summary",
        knn_config: Optional[str] = None,
        prompt_variant: Optional[str] = None,
        synthesis_model: Optional[str] = None,
        include_context: bool = False,
        language: Optional[str] = None,
        folder_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> RouteResult:
        """Execute Route 6: Community-aware concept synthesis.

        Pipeline:
          1. Community matching + Sentence vector search  (parallel)
          2. Denoise + Rerank sentence evidence
          3. Single LLM synthesis (community summaries + sentence evidence)

        Args:
            query: The user's natural language query.
            response_type: Response format ("summary", "detailed_report", etc.)
            knn_config: Unused (kept for interface compat).
            prompt_variant: Unused (kept for interface compat).
            synthesis_model: Optional override for synthesis LLM model.
            include_context: If True, include full LLM context in metadata.

        Returns:
            RouteResult with response, citations, and metadata.
        """
        # Resolve per-query folder scope (local variable — never mutate self.folder_id
        # to avoid cross-request leakage when the handler is shared across concurrent requests)
        folder_id = self._resolve_folder_id(folder_id)

        enable_timings = os.getenv("ROUTE6_RETURN_TIMINGS", "0").strip().lower() in {
            "1", "true", "yes",
        }
        timings_ms: Dict[str, int] = {}
        t_route_start = time.perf_counter()

        community_top_k = int(os.getenv("ROUTE6_COMMUNITY_TOP_K", "8"))
        rate_all_threshold = int(os.getenv("ROUTE6_RATE_ALL_THRESHOLD", "20"))
        sentence_top_k = int(os.getenv("ROUTE6_SENTENCE_TOP_K", "30"))
        section_top_k = int(os.getenv("ROUTE6_SECTION_TOP_K", "10"))

        logger.info(
            "route_6_start",
            query=query[:80],
            response_type=response_type,
            community_top_k=community_top_k,
            sentence_top_k=sentence_top_k,
            section_top_k=section_top_k,
        )

        # ================================================================
        # Step 1: Community Match + Sentence Search + Section Heading Search (PARALLEL)
        # ================================================================
        t0 = time.perf_counter()

        sentence_search_task = asyncio.create_task(
            self._retrieve_sentence_evidence(query, top_k=sentence_top_k, folder_id=folder_id)
        )
        section_search_task = asyncio.create_task(
            self._retrieve_section_headings(query, top_k=section_top_k, folder_id=folder_id)
        )

        # Upstream alignment: when the corpus is small (≤ rate_all_threshold),
        # skip embedding pre-filter and LLM-rate ALL communities.  This prevents
        # semantically distant but topically relevant communities from being cut
        # before the LLM ever sees them (root cause of Q-G8 / Q-G6 gaps).
        all_communities = await self.pipeline.community_matcher.get_all_communities()
        if len(all_communities) <= rate_all_threshold:
            # Shallow-copy dicts to avoid mutating the cached originals
            # (concurrent requests share the same CommunityMatcher cache)
            community_data = [dict(c) for c in all_communities]
            # Folder-scope prune: remove communities with no content in target folder
            if folder_id is not None:
                community_data = await self.pipeline.community_matcher.filter_communities_by_folder(
                    community_data, folder_id=folder_id,
                )
            community_scores = [1.0] * len(community_data)
            logger.info(
                "route6_rate_all_communities",
                total=len(community_data),
                threshold=rate_all_threshold,
            )
        else:
            matched_communities = await self.pipeline.community_matcher.match_communities(
                query, top_k=community_top_k, folder_id=folder_id,
            )
            # Shallow-copy dicts to avoid mutating the cached originals
            community_data = [dict(c) for c, _ in matched_communities]
            community_scores = [s for _, s in matched_communities]

        timings_ms["step_1_community_match_ms"] = int(
            (time.perf_counter() - t0) * 1000
        )

        logger.info(
            "route6_step_1_community_match",
            num_communities=len(community_data),
            titles=[c.get("title", "?") for c in community_data],
            top_scores=[round(s, 4) for s in community_scores[:5]],
        )

        # Feature 1: Dynamic Community Selection — LLM-rate matched communities
        dynamic_community = os.getenv(
            "ROUTE6_DYNAMIC_COMMUNITY", "1"
        ).strip().lower() in {"1", "true", "yes"}
        if dynamic_community and community_data:
            t_dc = time.perf_counter()
            try:
                community_data, community_scores = await self._rate_communities_with_llm(
                    query, community_data, community_scores,
                )
            except Exception as e:
                logger.warning("route6_dynamic_community_failed_fallback", error=str(e))
            timings_ms["step_1_dynamic_community_ms"] = int(
                (time.perf_counter() - t_dc) * 1000
            )

        # Feature 2: Community Children Traversal — expand with child communities
        community_children_enabled = os.getenv(
            "ROUTE6_COMMUNITY_CHILDREN", "0"
        ).strip().lower() in {"1", "true", "yes"}
        if community_children_enabled and community_data:
            t_cc = time.perf_counter()
            try:
                children = await self._fetch_community_children(
                    community_data, parent_scores=community_scores,
                    folder_id=folder_id,
                )
                if children:
                    # Dedup: skip children already in community_data
                    existing_ids = {c.get("id") for c in community_data}
                    added_count = 0
                    parent_count = len(community_data)
                    for child, child_score in children:
                        if child.get("id") not in existing_ids:
                            community_data.append(child)
                            community_scores.append(child_score)
                            existing_ids.add(child.get("id"))
                            added_count += 1
                    logger.info(
                        "route6_community_children_merged",
                        parent_count=parent_count,
                        children_added=added_count,
                        total=len(community_data),
                    )
            except Exception as e:
                logger.warning("route6_community_children_failed", error=str(e))
            timings_ms["step_1_community_children_ms"] = int(
                (time.perf_counter() - t_cc) * 1000
            )

        # Await sentence search
        try:
            sentence_evidence = await sentence_search_task
        except Exception as e:
            logger.warning("route6_sentence_search_failed", error=str(e))
            sentence_evidence = []

        # Await section heading search
        try:
            section_headings = await section_search_task
        except Exception as e:
            logger.warning("route6_section_search_failed", error=str(e))
            section_headings = []

        timings_ms["step_1_parallel_ms"] = int(
            (time.perf_counter() - t0) * 1000
        )

        logger.info(
            "route6_step_1_complete",
            communities=len(community_data),
            sentences_raw=len(sentence_evidence),
            sections=len(section_headings),
        )

        # ================================================================
        # Step 1b: R6-XII Entity-centric sentence expansion
        # After seed sentences are retrieved, traverse shared entities to
        # find additional related sentences for multi-hop reasoning.
        # ================================================================
        expansion_enabled = os.getenv(
            "ROUTE6_ENTITY_EXPANSION", "0"
        ).strip().lower() in {"1", "true", "yes"}
        expansion_count = 0
        expanded: List[Dict[str, Any]] = []

        if expansion_enabled and sentence_evidence:
            t_exp = time.perf_counter()
            exp_seeds = int(os.getenv("ROUTE6_ENTITY_EXPANSION_SEEDS", "10"))
            exp_top_k = int(os.getenv("ROUTE6_ENTITY_EXPANSION_TOP_K", "20"))
            exp_min_overlap = int(
                os.getenv("ROUTE6_ENTITY_EXPANSION_MIN_OVERLAP", "1")
            )

            try:
                expanded = await self._expand_sentences_via_entities(
                    seed_evidence=sentence_evidence,
                    seed_count=exp_seeds,
                    top_k=exp_top_k,
                    min_overlap=exp_min_overlap,
                    folder_id=folder_id,
                )
                if expanded:
                    expansion_count = len(expanded)
                    # Do NOT merge into sentence_evidence here — expanded
                    # sentences have synthetic scores that the diversity
                    # score_gate would filter out.  Keep them separate so
                    # they bypass diversity and go straight to the reranker.
                    logger.info(
                        "route6_entity_expansion_retrieved",
                        expanded_count=expansion_count,
                    )
            except Exception as e:
                logger.warning("route6_entity_expansion_failed", error=str(e))

            timings_ms["step_1b_entity_expansion_ms"] = int(
                (time.perf_counter() - t_exp) * 1000
            )

        # ================================================================
        # Step 2: Denoise + Rerank sentence evidence
        # ================================================================
        if sentence_evidence:
            t0 = time.perf_counter()
            raw_count = len(sentence_evidence)
            sentence_evidence = self._denoise_sentences(sentence_evidence)
            denoised_count = len(sentence_evidence)

            rerank_enabled = os.getenv(
                "ROUTE6_SENTENCE_RERANK", "1"
            ).strip().lower() in {"1", "true", "yes"}
            rerank_top_k = int(os.getenv("ROUTE6_RERANK_TOP_K", "15"))
            diversity_enabled = os.getenv(
                "ROUTE6_SENTENCE_DIVERSITY", "1"
            ).strip().lower() in {"1", "true", "yes"}
            min_per_doc = int(os.getenv("ROUTE6_SENTENCE_MIN_PER_DOC", "2"))
            score_gate = float(os.getenv("ROUTE6_SENTENCE_SCORE_GATE", "0.85"))

            # R6-6: Diversity BEFORE reranking but AFTER denoising (correct order).
            #
            #   Pipeline:
            #     1. Denoise  (removes junk sentences)
            #     2. Diversity → pool of 2×rerank_top_k (guarantees document coverage)
            #     3. Rerank   → final rerank_top_k from the diverse pool
            #
            #   The reranker picks the BEST sentences from a pool that already covers
            #   all qualifying documents, so both relevance and coverage are preserved.
            #
            #   Diversity activates whenever we have more evidence than rerank_top_k
            #   (previously required > 2×rerank_top_k, which was never met when
            #   the shared vector index limited raw results).
            if diversity_enabled and sentence_evidence:
                diversity_pool_k = rerank_top_k * 2
                if len(sentence_evidence) > rerank_top_k:
                    sentence_evidence = self._diversify_by_document(
                        sentence_evidence,
                        top_k=diversity_pool_k,
                        min_per_doc=min_per_doc,
                        score_gate=score_gate,
                    )

            # Inject entity-expanded sentences AFTER diversity, BEFORE reranking.
            # Expanded sentences carry synthetic scores that the diversity score_gate
            # would filter out.  By injecting them here the reranker (not the score
            # gate) decides whether they are relevant.
            if expanded:
                expanded_denoised = self._denoise_sentences(expanded)
                if expanded_denoised:
                    seen_ids = {ev.get("sentence_id") for ev in sentence_evidence}
                    seen_texts = {
                        (ev.get("text") or "")[:100].lower().strip()
                        for ev in sentence_evidence
                    }
                    for ev in expanded_denoised:
                        if ev.get("sentence_id") not in seen_ids:
                            txt_key = (ev.get("text") or "")[:100].lower().strip()
                            if txt_key in seen_texts:
                                continue
                            sentence_evidence.append(ev)
                            seen_ids.add(ev.get("sentence_id"))
                            seen_texts.add(txt_key)
                    logger.info(
                        "route6_expansion_injected_for_rerank",
                        injected=len(expanded_denoised),
                        rerank_pool=len(sentence_evidence),
                    )

            if rerank_enabled and sentence_evidence:
                # R6-3: Wrap in try/except — reranker failures must not crash the request.
                try:
                    sentence_evidence = await self._rerank_sentences(
                        query, sentence_evidence, top_k=rerank_top_k,
                    )
                except Exception as e:
                    logger.warning("route6_rerank_failed_fallback", error=str(e))
                    sentence_evidence = sentence_evidence[:rerank_top_k]

            timings_ms["step_2_denoise_rerank_ms"] = int(
                (time.perf_counter() - t0) * 1000
            )
            logger.info(
                "route6_step_2_denoise_rerank",
                raw=raw_count,
                after_denoise=denoised_count,
                after_rerank=len(sentence_evidence),
                rerank_enabled=rerank_enabled,
            )

        # ================================================================
        # Negative detection: no communities AND no sentences AND no sections
        # ================================================================
        if not community_data and not sentence_evidence and not section_headings:
            logger.info("route_6_negative_no_evidence")
            return RouteResult(
                response="The requested information was not found in the available documents.",
                route_used=self.ROUTE_NAME,
                citations=[],
                evidence_path=[],
                metadata={
                    "negative_detection": True,
                    "detection_reason": "no_communities_and_no_sentences",
                },
            )

        # ================================================================
        # Step 3: LLM synthesis (MAP-REDUCE or single-call)
        # ================================================================
        t0 = time.perf_counter()
        map_reduce = os.getenv(
            "ROUTE6_MAP_REDUCE_SYNTHESIS", "0"
        ).strip().lower() in {"1", "true", "yes"}

        if map_reduce:
            response_text = await self._map_reduce_synthesize(
                query, community_data, section_headings, sentence_evidence,
                language=language, folder_id=folder_id,
            )
        else:
            response_text = await self._synthesize(
                query, community_data, section_headings, sentence_evidence,
                language=language, folder_id=folder_id,
            )
        timings_ms["step_3_synthesis_ms"] = int(
            (time.perf_counter() - t0) * 1000
        )
        timings_ms["total_ms"] = int(
            (time.perf_counter() - t_route_start) * 1000
        )

        logger.info(
            "route6_step_3_complete",
            response_length=len(response_text),
            total_ms=timings_ms["total_ms"],
        )

        # ================================================================
        # Build citations
        # ================================================================
        citations = self._build_citations(
            community_data, community_scores, sentence_evidence,
        )
        await self._enrich_citations_with_geometry(citations)

        # ================================================================
        # Assemble metadata
        # ================================================================
        metadata: Dict[str, Any] = {
            "matched_communities": [c.get("title", "?") for c in community_data],
            "community_scores": {
                c.get("title", "?"): round(s, 4)
                for c, s in zip(community_data, community_scores)
            },
            "matched_sections": [s.get("title", "?") for s in section_headings],
            "section_scores": {
                s.get("title", "?"): round(s.get("score") or 0, 4)
                for s in section_headings
            },
            "sentence_evidence_count": len(sentence_evidence),
            "entity_expansion_enabled": expansion_enabled,
            "entity_expansion_count": expansion_count,
            "community_extract_enabled": os.getenv("ROUTE6_COMMUNITY_EXTRACT", "1").strip().lower() in {"1", "true", "yes"},
            "map_reduce_synthesis": map_reduce,
            "dynamic_community_enabled": dynamic_community,
            "community_children_enabled": community_children_enabled,
            "community_children_count": len([c for c in community_data if c.get("_is_child")]),
            "route_description": "Concept search — direct community synthesis (v2 + section headings)",
            "version": "v2",
        }

        if include_context:
            metadata["community_summaries"] = [
                {
                    "title": c.get("title", ""),
                    "summary": (c.get("summary") or "")[:300],
                    "score": round(s or 0, 4),
                }
                for c, s in zip(community_data, community_scores)
            ]
            metadata["section_headings"] = [
                {
                    "title": s.get("title", ""),
                    "summary": (s.get("summary") or "")[:300],
                    "path_key": s.get("path_key", ""),
                    "document_title": s.get("document_title", ""),
                    "score": round(s.get("score") or 0, 4),
                }
                for s in section_headings
            ]
            metadata["sentence_evidence"] = [
                {
                    "text": (s.get("text") or "")[:200],
                    "source": s.get("document_title", ""),
                    "section_path": s.get("section_path", ""),
                    "score": round(s.get("score") or 0, 4),
                    "expansion_source": s.get("expansion_source", ""),
                }
                for s in sentence_evidence[:10]
            ]

        if enable_timings:
            metadata["timings_ms"] = timings_ms

        return RouteResult(
            response=response_text,
            route_used=self.ROUTE_NAME,
            citations=citations,
            evidence_path=[c.get("title", "") for c in community_data],
            metadata=metadata,
        )

    # ==================================================================
    # Step 3: Single-call synthesis (NO MAP)
    # ==================================================================

    async def _synthesize(
        self,
        query: str,
        communities: List[Dict[str, Any]],
        section_headings: List[Dict[str, Any]],
        sentence_evidence: List[Dict[str, Any]],
        language: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> str:
        """Synthesize community summaries + section headings + sentence evidence in one LLM call.

        Unlike Route 3's MAP-REDUCE, community summaries are passed directly
        as thematic context — no per-community claim extraction.

        When ROUTE6_COMPLETENESS_CHECK is enabled, a second LLM pass verifies
        that all high-importance key points are represented in the answer.

        Args:
            query: User query.
            communities: Matched community dicts with title/summary.
            section_headings: Matched section dicts with title/summary/path_key.
            sentence_evidence: Denoised + reranked sentence dicts.
            folder_id: Folder scope for community source fetch (passed through).

        Returns:
            Synthesized response text.
        """
        # Build the synthesis prompt (shared with _stream_synthesize)
        prompt, summaries_text = await self._build_synthesis_prompt(
            query, communities, section_headings, sentence_evidence,
            language=language, folder_id=folder_id,
        )

        try:
            response = await acomplete_with_retry(self.llm, prompt)
            answer = response.text.strip()
        except Exception as e:
            logger.error(
                "route6_synthesis_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return (
                "An error occurred while synthesizing the response. "
                f"Please try again. (Error: {type(e).__name__})"
            )

        # Two-pass completeness check
        completeness_check = os.getenv(
            "ROUTE6_COMPLETENESS_CHECK", "1"
        ).strip().lower() in {"1", "true", "yes"}

        if completeness_check and summaries_text and "(No thematic context" not in summaries_text:
            answer = await self._completeness_check(query, summaries_text, answer)

        return answer

    async def _completeness_check(
        self,
        query: str,
        key_points: str,
        answer: str,
    ) -> str:
        """Second LLM pass: identify high-importance key points missing from the answer.

        If any key points with importance ≥ 70 are missing, their content is
        appended to the answer as additional details. The original answer is
        never rewritten — only additive.

        Args:
            query: Original user query.
            key_points: Formatted key-points text (from extraction).
            answer: Initial synthesis answer.

        Returns:
            Original answer with missing items appended (or unchanged if complete).
        """
        t0 = time.perf_counter()
        prompt = SYNTHESIS_COMPLETENESS_CHECK_PROMPT.format(
            query=query,
            key_points=key_points,
            answer=answer,
        )

        try:
            response = await acomplete_with_retry(self.llm, prompt)
            result = response.text.strip()
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            if "ALL_COMPLETE" in result and len(result) < 50:
                logger.info(
                    "route6_completeness_check_done",
                    changed=False,
                    elapsed_ms=elapsed_ms,
                )
                return answer

            # Append missing items to the original answer
            if result and len(result) > 10:
                patched = answer.rstrip() + "\n\n" + result.strip()
                logger.info(
                    "route6_completeness_check_done",
                    changed=True,
                    original_len=len(answer),
                    addendum_len=len(result),
                    patched_len=len(patched),
                    elapsed_ms=elapsed_ms,
                )
                return patched
            else:
                logger.info(
                    "route6_completeness_check_done",
                    changed=False,
                    elapsed_ms=elapsed_ms,
                )
                return answer
        except Exception as e:
            logger.error(
                "route6_completeness_check_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return answer  # graceful fallback — return original answer

    # ==================================================================
    # MAP-REDUCE Synthesis (per-community MAP → merge REDUCE)
    # ==================================================================

    async def _map_reduce_synthesize(
        self,
        query: str,
        communities: List[Dict[str, Any]],
        section_headings: List[Dict[str, Any]],
        sentence_evidence: List[Dict[str, Any]],
        language: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> str:
        """MAP-REDUCE synthesis: per-community MAP → merge REDUCE.

        MAP phase: For each community's key points, generate a focused
        mini-answer. Each MAP call sees only 3-5 points → can't
        non-deterministically drop items.

        REDUCE phase: Merge all community mini-answers + sentence evidence
        + section headings into the final organized response.

        Falls back to single-call synthesis when extraction is disabled
        or produces no structured points.
        """
        community_extract = os.getenv(
            "ROUTE6_COMMUNITY_EXTRACT", "1"
        ).strip().lower() in {"1", "true", "yes"}

        if community_extract and communities:
            summaries_text, points = await self._extract_community_key_points(
                query, communities, folder_id=folder_id,
            )
        else:
            return await self._synthesize(
                query, communities, section_headings, sentence_evidence,
                language=language, folder_id=folder_id,
            )

        if not points or "(No thematic context" in summaries_text:
            return await self._synthesize(
                query, communities, section_headings, sentence_evidence,
                language=language, folder_id=folder_id,
            )

        # Group key points by community
        by_community: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for p in points:
            by_community[p.get("community", "General")].append(p)

        logger.info(
            "route6_map_reduce_synthesis_start",
            num_communities=len(by_community),
            total_points=len(points),
            points_per_community={k: len(v) for k, v in by_community.items()},
        )

        # MAP phase: parallel per-community synthesis
        max_concurrent = int(os.getenv("ROUTE6_MAP_SYNTHESIS_CONCURRENCY", "12"))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _map_one(community_title: str, community_points: List[Dict[str, Any]]) -> str:
            kp_lines = []
            for p in community_points:
                desc = p.get("description", "")
                score = p.get("score", 0)
                kp_lines.append(f"- (importance: {score}) {desc}")
            kp_text = "\n".join(kp_lines)

            prompt = COMMUNITY_MAP_SYNTHESIS_PROMPT.format(
                query=query,
                community_title=community_title,
                community_key_points=kp_text,
            )
            async with semaphore:
                try:
                    resp = await acomplete_with_retry(self.llm, prompt)
                    return resp.text.strip()
                except Exception as e:
                    logger.warning(
                        "route6_map_synthesis_one_failed",
                        community=community_title,
                        error=str(e),
                    )
                    return kp_text  # fallback: raw key points

        t0 = time.perf_counter()
        community_items = list(by_community.items())
        tasks = [_map_one(title, pts) for title, pts in community_items]
        map_results = await asyncio.gather(*tasks)
        map_ms = int((time.perf_counter() - t0) * 1000)

        # Format community responses for REDUCE
        community_response_blocks = []
        for (title, _), mini_answer in zip(community_items, map_results):
            community_response_blocks.append(f"--- {title} ---\n{mini_answer}")
        community_text = "\n\n".join(community_response_blocks)

        # Format section headings
        if section_headings:
            heading_lines = []
            for i, sec in enumerate(section_headings, 1):
                title = sec.get("title", f"Section {i}")
                doc_title = sec.get("document_title", "")
                path_key = sec.get("path_key", "").strip()
                parts = []
                if doc_title:
                    parts.append(f"[{doc_title}]")
                if path_key and path_key != title:
                    parts.append(path_key)
                else:
                    parts.append(title)
                heading_lines.append(f"- {' '.join(parts)}")
            headings_text = "\n".join(heading_lines)
        else:
            headings_text = "(No document structure available)"

        # Format sentence evidence
        if sentence_evidence:
            evidence_lines = []
            for i, ev in enumerate(sentence_evidence, 1):
                doc = ev.get("document_title") or "Unknown"
                section = ev.get("section_path") or ""
                text = ev.get("text") or ""
                if section:
                    evidence_lines.append(f"{i}. [{doc} > {section}] {text}")
                else:
                    evidence_lines.append(f"{i}. [{doc}] {text}")
            evidence_text = "\n".join(evidence_lines)
        else:
            evidence_text = "(No additional document evidence)"

        # REDUCE: merge community responses + evidence → final answer
        reduce_prompt = REDUCE_SYNTHESIS_PROMPT.format(
            query=query,
            community_responses=community_text,
            section_headings=headings_text,
            sentence_evidence=evidence_text,
        )

        if language:
            reduce_prompt += f"\n\nIMPORTANT: Respond entirely in {language}."

        try:
            t1 = time.perf_counter()
            response = await acomplete_with_retry(self.llm, reduce_prompt)
            answer = response.text.strip()
            reduce_ms = int((time.perf_counter() - t1) * 1000)
        except Exception as e:
            logger.error("route6_reduce_synthesis_failed", error=str(e))
            return (
                "An error occurred while synthesizing the response. "
                f"Please try again. (Error: {type(e).__name__})"
            )

        logger.info(
            "route6_map_reduce_synthesis_done",
            map_calls=len(community_items),
            map_ms=map_ms,
            reduce_ms=reduce_ms,
            total_ms=map_ms + reduce_ms,
            answer_length=len(answer),
        )

        # Completeness check (same as single-call)
        completeness_check = os.getenv(
            "ROUTE6_COMPLETENESS_CHECK", "1"
        ).strip().lower() in {"1", "true", "yes"}

        if completeness_check and summaries_text and "(No thematic context" not in summaries_text:
            answer = await self._completeness_check(query, summaries_text, answer)

        return answer

    # ==================================================================
    # Feature 1: Dynamic Community Selection (LLM-rated)
    # ==================================================================

    # Upstream-aligned rating prompt with chain-of-thought reasoning.
    # Key improvements over the original:
    #  1. "even if only partially relevant" — inclusive rating language
    #  2. "reason" field — forces LLM to think before scoring
    #  3. Entity names in context — richer signal for relevance
    _COMMUNITY_RATING_PROMPT = (
        "You are deciding whether the following information is useful for "
        "answering a question, even if it is only partially relevant.\n\n"
        "---Information---\n"
        "Community: {title}\n"
        "{summary}\n"
        "{entities}\n\n"
        "---Question---\n"
        "{query}\n\n"
        "Respond with ONLY a JSON object:\n"
        "{{\"reason\": \"brief reasoning for your rating\", \"rating\": <0-5>}}\n"
        "0 = completely irrelevant, 5 = perfectly relevant.\n"
        "Rate generously — even partial or indirect relevance should score ≥ 1."
    )

    async def _rate_communities_with_llm(
        self,
        query: str,
        communities: List[Dict[str, Any]],
        scores: List[float],
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        """Rate matched communities using the pipeline LLM, filter low-rated ones.

        Inspired by Microsoft GraphRAG's DynamicCommunitySelection. Rates each
        community's relevance on a 0-5 scale, then filters below threshold.

        Note: uses self.llm (the main synthesis model).  For lower cost,
        consider setting ROUTE6_DYNAMIC_COMMUNITY=0 and relying on embedding
        pre-filtering alone.

        Args:
            query: User query.
            communities: Community dicts from embedding match.
            scores: Corresponding cosine similarity scores.

        Returns:
            Filtered (communities, scores) tuple.
        """
        threshold = int(os.getenv("ROUTE6_DYNAMIC_COMMUNITY_THRESHOLD", "1"))
        max_concurrent = int(os.getenv("ROUTE6_DYNAMIC_COMMUNITY_CONCURRENCY", "12"))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _rate_one(community: Dict[str, Any]) -> int:
            # Build entity context for richer signal (Priority 3)
            entity_names = community.get("entity_names", [])
            entities_text = (
                f"Key entities: {', '.join(entity_names[:15])}"
                if entity_names else ""
            )
            prompt = self._COMMUNITY_RATING_PROMPT.format(
                query=query,
                title=community.get("title", ""),
                summary=(community.get("summary", "") or "")[:500],
                entities=entities_text,
            )
            async with semaphore:
                resp = None
                try:
                    resp = await acomplete_with_retry(self.llm, prompt)
                    text = resp.text.strip()
                    if text.startswith("```"):
                        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
                        text = re.sub(r'\n?```\s*$', '', text)
                    parsed = json.loads(text)
                    return int(parsed.get("rating", 0))
                except (json.JSONDecodeError, ValueError, KeyError):
                    # Try extracting a bare number
                    raw = resp.text if resp else ""
                    match = re.search(r"\b(\d+)\b", raw)
                    return int(match.group(1)) if match else 0
                except Exception as e:
                    logger.warning("route6_community_rating_error", error=str(e))
                    return -1  # -1 means "keep" (LLM failure → don't filter)

        # Rate all communities concurrently
        ratings = await asyncio.gather(*[_rate_one(c) for c in communities])

        # Filter below threshold; keep communities where LLM failed (rating == -1)
        rated_triples = []
        for community, score, rating in zip(communities, scores, ratings):
            if rating == -1 or rating >= threshold:
                rated_triples.append((community, score, rating))

        # Sort by LLM rating descending (upstream alignment: highest-rated first)
        rated_triples.sort(key=lambda t: t[2], reverse=True)
        filtered_communities = [t[0] for t in rated_triples]
        filtered_scores = [t[1] for t in rated_triples]

        # Attach LLM rating to community dict for downstream use (extraction cutoff)
        for community, _, rating in rated_triples:
            community["_llm_rating"] = rating

        logger.info(
            "route6_dynamic_community_ratings",
            ratings=list(zip(
                [c.get("title", "?") for c in filtered_communities],
                [t[2] for t in rated_triples],
            )),
            threshold=threshold,
            kept=len(filtered_communities),
            dropped=len(communities) - len(filtered_communities),
        )

        # If all were filtered out, return original (safety fallback)
        if not filtered_communities:
            logger.warning("route6_dynamic_community_all_filtered_fallback")
            return communities, scores

        return filtered_communities, filtered_scores

    # ==================================================================
    # Feature 1b: Community Source-Text MAP (Microsoft-aligned)
    # ==================================================================

    async def _fetch_community_source_sentences(
        self,
        communities: List[Dict[str, Any]],
        max_per_community: int = 50,
        folder_id: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch source sentences for matched communities via graph traversal.

        Traverses Community → BELONGS_TO → Entity → MENTIONS → Sentence
        to retrieve the actual document text that belongs to each community.
        This aligns with Microsoft's LazyGraphRAG MAP phase which extracts
        claims from source text, not from abstract community summaries.

        Args:
            communities: Matched community dicts (must have 'id' field).
            max_per_community: Max sentences per community (dedup'd).
            folder_id: Folder scope filter (None = all folders).

        Returns:
            Dict mapping community_id → list of sentence dicts with
            text, document_title, section_path, sentence_id.
        """
        if not self.neo4j_driver:
            logger.warning("route6_community_source_no_neo4j_driver")
            return {}

        community_ids = [c.get("id") for c in communities if c.get("id")]
        if not community_ids:
            return {}

        group_ids = self.group_ids

        folder_filter_clause = (
            "WITH s, doc, c_id\n"
            "        WHERE $folder_id IS NULL OR doc IS NULL"
            " OR EXISTS { MATCH (doc)-[:IN_FOLDER]->(f:Folder)"
            " WHERE f.id = $folder_id AND f.group_id IN $group_ids }\n"
        )

        # Fetch entity-linked sentences via Community→Entity→MENTIONS→Sentence
        # graph traversal.

        cypher = f"""
        UNWIND $community_ids AS c_id
        MATCH (c:Community {{id: c_id}})
        WHERE c.group_id IN $group_ids
        MATCH (c)<-[:BELONGS_TO]-(e:Entity)
        WHERE e.group_id IN $group_ids
        MATCH (e)<-[:MENTIONS]-(s:Sentence)
        WHERE s.group_id IN $group_ids AND s.text IS NOT NULL
        OPTIONAL MATCH (s)-[:IN_DOCUMENT]->(doc:Document)

        {folder_filter_clause}
        WITH c_id, s, doc
        RETURN DISTINCT c_id AS community_id,
               s.id AS sentence_id,
               s.text AS text,
               s.section_path AS section_path,
               s.page AS page,
               doc.title AS document_title
        ORDER BY c_id, s.page, s.id
        """

        try:
            loop = asyncio.get_running_loop()
            driver = self.neo4j_driver

            def _run():
                with retry_session(driver, read_only=True) as session:
                    records = session.run(
                        cypher,
                        community_ids=community_ids,
                        group_ids=group_ids,
                        folder_id=folder_id,
                    )
                    return [dict(r) for r in records]

            results = await loop.run_in_executor(self._executor, _run)
        except Exception as e:
            logger.warning("route6_community_source_query_failed", error=str(e))
            return {}

        # Group by community, dedup by sentence_id, cap per community
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        seen: Dict[str, set] = defaultdict(set)
        for r in results:
            cid = r["community_id"]
            sid = r["sentence_id"]
            if sid in seen[cid]:
                continue
            seen[cid].add(sid)
            if len(grouped[cid]) < max_per_community:
                grouped[cid].append(r)

        total = sum(len(v) for v in grouped.values())
        logger.info(
            "route6_community_source_fetched",
            num_communities=len(grouped),
            total_sentences=total,
        )
        return dict(grouped)

    async def _extract_community_key_points(
        self,
        query: str,
        communities: List[Dict[str, Any]],
        folder_id: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Extract query-relevant key points from community SOURCE TEXT.

        True MAP pattern (upstream-aligned):
        1. For each matched community, fetch actual source sentences
           via Community → Entity → MENTIONS → Sentence graph traversal.
        2. Extract key points from top-rated communities INDIVIDUALLY in parallel.
           This gives each community focused LLM attention (prevents large
           combined contexts from causing detail loss).
        3. Lower-rated communities use raw summaries (no LLM call) to save latency.
        4. Aggregate, deduplicate, sort, and filter all key points.

        Falls back to raw summaries if source fetch fails.

        Returns:
            Tuple of (formatted_text, structured_points). structured_points is the
            deduplicated/filtered list of dicts (description, score, community).
        """
        extract_top_k = int(os.getenv("ROUTE6_EXTRACT_TOP_K", "12"))
        extract_min_rating = int(os.getenv("ROUTE6_EXTRACT_MIN_RATING", "1"))

        # Fetch source sentences only for communities we'll extract from.
        # Communities list is pre-sorted by LLM rating (highest first).
        # Apply both a count cap (top_k) and a rating floor (min_rating).
        extract_communities = [
            c for c in communities[:extract_top_k]
            if c.get("_llm_rating", 5) >= extract_min_rating
        ]
        extract_ids = {c.get("id") for c in extract_communities}
        summary_communities = [c for c in communities if c.get("id") not in extract_ids]

        source_map = await self._fetch_community_source_sentences(
            extract_communities, folder_id=folder_id,
        )

        # Build per-community source text blocks for extraction
        community_texts: List[Tuple[Dict[str, Any], str]] = []
        for i, c in enumerate(extract_communities, 1):
            title = c.get("title", f"Theme {i}")
            cid = c.get("id", "")
            sentences = source_map.get(cid, [])

            if sentences:
                by_doc: Dict[str, List[str]] = defaultdict(list)
                for s in sentences:
                    doc = s.get("document_title") or "Unknown"
                    text = (s.get("text") or "").strip()
                    if text:
                        by_doc[doc].append(text)

                doc_sections = []
                for doc_title, texts in by_doc.items():
                    joined = " ".join(texts)
                    doc_sections.append(f"  [{doc_title}]: {joined}")
                source_text = "\n".join(doc_sections)
                community_texts.append((c, f"--- Community: {title} ---\n{source_text}"))
            else:
                summary = (c.get("summary") or "").strip()
                if summary:
                    community_texts.append((c, f"--- Community: {title} ---\n  {summary}"))

        if not community_texts and not summary_communities:
            return "(No thematic context available)", []

        logger.info(
            "route6_extract_source_stats",
            total_communities=len(communities),
            extract_communities=len(community_texts),
            summary_only_communities=len(summary_communities),
            source_text_chars=sum(len(t) for _, t in community_texts),
        )

        # MAP phase: per-community parallel extraction for top-rated communities.
        # Each community gets its own LLM call for focused attention.
        # All calls run concurrently — wall-clock time ≈ slowest single call.
        max_concurrent = int(os.getenv("ROUTE6_EXTRACT_CONCURRENCY", "12"))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _extract_one(community: Dict[str, Any], source_block: str) -> List[Dict[str, Any]]:
            title = community.get("title", "?")
            prompt = COMMUNITY_EXTRACT_PROMPT.format(
                query=query,
                community_source_text=source_block,
            )
            async with semaphore:
                try:
                    resp = await acomplete_with_retry(self.llm, prompt)
                    text = resp.text.strip()
                    if text.startswith("```"):
                        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
                        text = re.sub(r'\n?```\s*$', '', text)
                    parsed = json.loads(text)
                    points = parsed.get("points", [])
                    for p in points:
                        if not p.get("community"):
                            p["community"] = title
                    return points
                except (json.JSONDecodeError, ValueError):
                    logger.warning("route6_extract_one_parse_error", community=title)
                    return []
                except Exception as e:
                    logger.warning("route6_extract_one_failed", community=title, error=str(e))
                    return []

        if community_texts:
            tasks = [_extract_one(c, txt) for c, txt in community_texts]
            results = await asyncio.gather(*tasks)
        else:
            results = []

        # REDUCE phase: aggregate all points, deduplicate, sort, filter
        all_points: List[Dict[str, Any]] = []
        for pts in results:
            all_points.extend(pts)

        if not all_points:
            logger.info("route6_community_extract_no_points")
            return self._format_raw_summaries(communities), []

        # Deduplicate by description similarity (exact match on first 60 chars)
        seen_descs: set = set()
        unique_points = []
        for p in all_points:
            key = (p.get("description", "")[:60]).lower().strip()
            if key not in seen_descs:
                seen_descs.add(key)
                unique_points.append(p)

        # Sort by score descending, filter low-importance
        unique_points.sort(key=lambda p: p.get("score", 0), reverse=True)
        min_score = int(os.getenv("ROUTE6_EXTRACT_MIN_SCORE", "20"))
        points = [p for p in unique_points if p.get("score", 0) >= min_score]
        if not points:
            return self._format_raw_summaries(communities), []

        # Cap key points to keep synthesis prompt tractable (reduces latency)
        max_points = int(os.getenv("ROUTE6_MAX_EXTRACT_POINTS", "30"))
        points = points[:max_points]

        formatted = []
        for p in points:
            desc = p.get("description", "")
            score = p.get("score", 0)
            community = p.get("community", "")
            tag = f" [{community}]" if community else ""
            formatted.append(f"- (importance: {score}) {desc}{tag}")

        # Append raw summaries for ALL communities as fallback context.
        # Extracted communities get both focused key-points above AND their
        # raw summary below, so synthesis never loses information that the
        # extraction LLM filtered out too aggressively (fixes Q-G7 regression
        # where "60 days written notice" etc. were dropped by extraction).
        all_summary_communities = extract_communities + summary_communities
        if all_summary_communities:
            formatted.append("")
            formatted.append("--- Thematic Summaries (broad context) ---")
            for c in all_summary_communities:
                title = c.get("title", "?")
                summary = (c.get("summary") or "").strip()
                if summary:
                    formatted.append(f"- [{title}]: {summary[:200]}")

        logger.info(
            "route6_community_extract_done",
            total_raw=len(all_points),
            after_dedup=len(unique_points),
            after_filter=len(points),
            max_points=max_points,
            summary_appended=len(all_summary_communities),
            top_score=points[0].get("score", 0) if points else 0,
        )
        return "\n".join(formatted), points

    @staticmethod
    def _format_raw_summaries(communities: List[Dict[str, Any]]) -> str:
        """Format communities as raw summary text (fallback)."""
        lines = []
        for i, c in enumerate(communities, 1):
            title = c.get("title", f"Theme {i}")
            summary = (c.get("summary") or "").strip()
            if summary:
                lines.append(f"{i}. **{title}**: {summary}")
        return "\n".join(lines) if lines else "(No thematic context available)"

    # ==================================================================
    # Feature 2: Community Children Traversal
    # ==================================================================

    async def _fetch_community_children(
        self,
        parent_communities: List[Dict[str, Any]],
        parent_scores: Optional[List[float]] = None,
        folder_id: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Fetch child communities via PARENT_COMMUNITY edges in Neo4j.

        For each parent community, traverses the hierarchy built by
        ensure_community_hierarchy() to find finer-grained child communities.

        Args:
            parent_communities: Matched parent community dicts.
            folder_id: Folder scope filter (None = all folders).

        Returns:
            List of (child_community_dict, synthetic_score) tuples.
        """
        if not self.neo4j_driver:
            return []

        max_depth = int(os.getenv("ROUTE6_COMMUNITY_CHILDREN_MAX_LEVEL", "1"))
        parent_ids = [c.get("id") for c in parent_communities if c.get("id")]
        if not parent_ids:
            return []

        group_ids = self.group_ids

        # Fetch children up to max_depth levels below parents.
        # Neo4j doesn't support parameterised path lengths, so interpolate
        # the int directly (safe — comes from int()).
        cypher = f"""
        UNWIND $parent_ids AS pid
        MATCH (child:Community)-[:PARENT_COMMUNITY*1..{max_depth}]->(parent:Community {{id: pid}})
        WHERE child.group_id IN $group_ids AND parent.group_id IN $group_ids
              AND child.summary IS NOT NULL AND child.summary <> ''
        WITH DISTINCT child, parent
        RETURN child.id AS id,
               child.title AS title,
               child.summary AS summary,
               child.level AS level,
               child.rank AS rank,
               parent.id AS parent_id
        ORDER BY child.rank DESC
        """

        try:
            loop = asyncio.get_running_loop()
            driver = self.neo4j_driver

            def _run():
                with retry_session(driver, read_only=True) as session:
                    records = session.run(
                        cypher,
                        parent_ids=parent_ids,
                        group_ids=group_ids,
                    )
                    return [dict(r) for r in records]

            results = await loop.run_in_executor(self._executor, _run)
        except Exception as e:
            logger.warning("route6_community_children_query_failed", error=str(e))
            return []

        if not results:
            return []

        # Assign synthetic score (below parent minimum)
        if parent_scores:
            synthetic_score = min(parent_scores) * 0.8
        else:
            synthetic_score = 0.3

        children: List[Tuple[Dict[str, Any], float]] = []
        for r in results:
            child_dict = {
                "id": r["id"],
                "title": r.get("title", ""),
                "summary": r.get("summary", ""),
                "level": r.get("level", 0),
                "rank": r.get("rank", 0),
                "parent_id": r.get("parent_id", ""),
                "_is_child": True,  # marker for metadata traceability
            }
            children.append((child_dict, synthetic_score))

        # Folder-scope filter: prune children whose entities have no content
        # in the target folder (same pattern as CommunityMatcher._filter_communities_by_folder).
        if folder_id is not None and children:
            child_ids = [c.get("id") for c, _ in children if c.get("id")]
            folder_cypher = """
            UNWIND $child_ids AS cid
            MATCH (c:Community {id: cid})
            WHERE c.group_id IN $group_ids
            MATCH (c)<-[:BELONGS_TO]-(e:Entity)
                  <-[:MENTIONS]-(tc:Sentence)
                  -[:IN_DOCUMENT]->(d:Document)
                  -[:IN_FOLDER]->(f:Folder {id: $folder_id})
            WHERE tc.group_id IN $group_ids
              AND d.group_id IN $group_ids
              AND f.group_id IN $group_ids
            RETURN DISTINCT cid
            """
            try:
                def _run_folder_check():
                    with retry_session(driver, read_only=True) as session:
                        records = session.run(
                            folder_cypher,
                            child_ids=child_ids,
                            group_ids=group_ids,
                            folder_id=folder_id,
                        )
                        return {dict(r)["cid"] for r in records}

                valid_ids = await loop.run_in_executor(self._executor, _run_folder_check)
                before = len(children)
                children = [(c, s) for c, s in children if c.get("id") in valid_ids]
                if len(children) < before:
                    logger.info(
                        "route6_community_children_folder_filter",
                        folder_id=folder_id,
                        before=before,
                        after=len(children),
                    )
            except Exception as e:
                logger.warning("route6_community_children_folder_filter_failed", error=str(e))

        logger.info(
            "route6_community_children_fetched",
            parent_count=len(parent_ids),
            children_count=len(children),
            child_titles=[c.get("title", "?") for c, _ in children[:5]],
        )

        return children

    # ==================================================================
    # Shared prompt builder (used by _synthesize and _stream_synthesize)
    # ==================================================================

    async def _build_synthesis_prompt(
        self,
        query: str,
        communities: List[Dict[str, Any]],
        section_headings: List[Dict[str, Any]],
        sentence_evidence: List[Dict[str, Any]],
        language: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Build the full synthesis prompt. Shared by _synthesize and _stream_synthesize.

        Returns:
            Tuple of (prompt, summaries_text) — summaries_text is the key-points
            text used for completeness checking.
        """
        # Format community summaries
        community_extract = os.getenv(
            "ROUTE6_COMMUNITY_EXTRACT", "1"
        ).strip().lower() in {"1", "true", "yes"}

        if community_extract and communities:
            summaries_text, _ = await self._extract_community_key_points(
                query, communities, folder_id=folder_id,
            )
        elif communities:
            summary_lines = []
            for i, c in enumerate(communities, 1):
                title = c.get("title", f"Theme {i}")
                summary = (c.get("summary") or "").strip()
                if summary:
                    summary_lines.append(f"{i}. **{title}**: {summary}")
                else:
                    entities = ", ".join(c.get("entity_names", [])[:10])
                    if entities:
                        summary_lines.append(f"{i}. **{title}**: Entities: {entities}")
            summaries_text = "\n".join(summary_lines) if summary_lines else "(No thematic context available)"
        else:
            summaries_text = "(No thematic context available)"

        # Format section headings
        if section_headings:
            heading_lines = []
            for i, sec in enumerate(section_headings, 1):
                title = sec.get("title", f"Section {i}")
                doc_title = sec.get("document_title", "")
                path_key = sec.get("path_key", "").strip()
                parts = []
                if doc_title:
                    parts.append(f"[{doc_title}]")
                if path_key and path_key != title:
                    parts.append(path_key)
                else:
                    parts.append(title)
                heading_lines.append(f"- {' '.join(parts)}")
            headings_text = "\n".join(heading_lines)
        else:
            headings_text = "(No document structure available)"

        # Format sentence evidence
        if sentence_evidence:
            evidence_lines = []
            for i, ev in enumerate(sentence_evidence, 1):
                doc = ev.get("document_title") or "Unknown"
                section = ev.get("section_path") or ""
                text = ev.get("text") or ""
                if section:
                    evidence_lines.append(f"{i}. [{doc} > {section}] {text}")
                else:
                    evidence_lines.append(f"{i}. [{doc}] {text}")
            evidence_text = "\n".join(evidence_lines)
        else:
            evidence_text = "(No document evidence retrieved)"

        # Feature 4: Token budget
        max_tokens = int(os.getenv("ROUTE6_MAX_CONTEXT_TOKENS", "0"))
        if max_tokens > 0:
            summaries_tokens = len(_tiktoken_enc.encode(summaries_text))
            sections = [
                ("evidence", evidence_text),
                ("headings", headings_text),
            ]
            other_tokens = sum(len(_tiktoken_enc.encode(t)) for _, t in sections)
            total = summaries_tokens + other_tokens
            if total > max_tokens:
                # If community summaries alone exceed the budget, truncate them
                # to 70% of budget so evidence always gets at least 30%.
                if summaries_tokens > max_tokens:
                    summary_cap = int(max_tokens * 0.7)
                    summary_tokens_list = _tiktoken_enc.encode(summaries_text)
                    summaries_text = _tiktoken_enc.decode(summary_tokens_list[:summary_cap])
                    summaries_tokens = summary_cap
                budget = max(max_tokens - summaries_tokens, 0)
                truncated = {}
                for name, text in sections:
                    tokens = _tiktoken_enc.encode(text)
                    if len(tokens) <= budget:
                        truncated[name] = text
                        budget -= len(tokens)
                    else:
                        truncated[name] = _tiktoken_enc.decode(tokens[:max(budget, 0)])
                        budget = 0
                evidence_text = truncated["evidence"]
                headings_text = truncated["headings"]

        prompt = CONCEPT_SYNTHESIS_PROMPT.format(
            query=query,
            community_summaries=summaries_text,
            section_headings=headings_text,
            sentence_evidence=evidence_text,
        )

        if language:
            prompt += f"\n\nIMPORTANT: Respond entirely in {language}."

        return prompt, summaries_text

    async def _retrieve_sentence_evidence(
        self,
        query: str,
        top_k: int = 20,
        folder_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve sentence-level evidence via Voyage vector search.

        Reuses the same sentence index that Route 3 uses (sentence_embedding).
        Document diversity ensures minority documents get representation.

        Args:
            query: User query to embed and search.
            top_k: Max sentences to retrieve.
            folder_id: Folder scope filter (None = all folders).

        Returns:
            List of sentence dicts with text, metadata, and score.
        """
        voyage_service = _get_voyage_service()
        if not voyage_service:
            logger.warning("route6_sentence_search_no_voyage_service")
            return []

        if not self.neo4j_driver:
            logger.warning("route6_sentence_search_no_neo4j_driver")
            return []

        # 1. Embed query with Voyage (sync HTTP call — run off event loop)
        try:
            loop = asyncio.get_running_loop()
            query_embedding = await loop.run_in_executor(
                self._executor, voyage_service.embed_query, query,
            )
        except Exception as e:
            logger.warning("route6_sentence_embed_failed", error=str(e))
            return []

        threshold = float(os.getenv("ROUTE6_SENTENCE_THRESHOLD", "0.2"))
        # R6-6: Fetch 3x for denoising headroom; diversity is applied AFTER reranking
        # in execute() so there is no need for diversity logic inside this method.
        fetch_k = top_k * 3
        group_ids = self.group_ids

        # R6-1: Build folder filter clause — applied AFTER OPTIONAL MATCH for doc.
        # Uses Cypher's IS NULL test so the WHERE is a no-op when no folder scope is set.
        folder_filter_clause = (
            "// R6-1: folder scope filter (no-op when $folder_id IS NULL)\n"
            "        WITH sent, score, doc, sec, prev_sent, next_sent\n"
            "        WHERE $folder_id IS NULL OR doc IS NULL"
            " OR EXISTS { MATCH (doc)-[:IN_FOLDER]->(f:Folder)"
            " WHERE f.id = $folder_id AND f.group_id IN $group_ids }\n"
        )

        # 2. Vector search on Sentence nodes + collect parent context.
        # sentence_embedding index has group_id as a filterable property
        # (WITH [s.group_id]), so use UNION ALL for in-index filtering
        # across tenant + __global__ groups.
        # Skip duplicate UNION branch when group_id == global_group_id.
        if self.group_id == settings.GLOBAL_GROUP_ID:
            search_clause = """CYPHER 25
        MATCH (sent:Sentence)
        SEARCH sent IN (VECTOR INDEX sentence_embedding FOR $embedding WHERE sent.group_id = $group_id LIMIT $top_k)
        SCORE AS score
        WHERE score >= $threshold
        """
        else:
            search_clause = """CYPHER 25
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
        """

        cypher = f"""{search_clause}

        // Get document + section context
        OPTIONAL MATCH (sent)-[:IN_DOCUMENT]->(doc:Document)
        OPTIONAL MATCH (sent)-[:IN_SECTION]->(sec:Section)

        // Expand via NEXT for local context (1 hop each direction)
        OPTIONAL MATCH (sent)-[:NEXT]->(next_sent:Sentence)
        OPTIONAL MATCH (prev_sent:Sentence)-[:NEXT]->(sent)

        {folder_filter_clause}
        RETURN sent.id AS sentence_id,
               sent.text AS text,
               sent.source AS source,
               sent.section_path AS section_path,
               sec.path_key AS section_key,
               sent.page AS page,
               sent.parent_text AS chunk_text,
               doc.title AS document_title,
               doc.id AS document_id,
               score,
               prev_sent.text AS prev_text,
               next_sent.text AS next_text
        ORDER BY score DESC
        """

        try:
            loop = asyncio.get_running_loop()
            driver = self.neo4j_driver

            def _run_search():
                with retry_session(driver, read_only=True) as session:
                    records = session.run(
                        cypher,
                        embedding=query_embedding,
                        group_id=self.group_id,
                        global_group_id=settings.GLOBAL_GROUP_ID,
                        group_ids=group_ids,
                        top_k=fetch_k,
                        threshold=threshold,
                        folder_id=folder_id,
                    )
                    return [dict(r) for r in records]

            results = await loop.run_in_executor(self._executor, _run_search)
        except Exception as e:
            logger.warning("route6_sentence_search_failed", error=str(e))
            return []

        if not results:
            logger.info("route6_sentence_search_empty", query=query[:50])
            return []

        # 3. Deduplicate by sentence_id and build context passages
        seen_sentences: set = set()
        seen_texts: set = set()
        evidence: List[Dict[str, Any]] = []

        for r in results:
            sid = r.get("sentence_id", "")
            if sid in seen_sentences:
                continue
            seen_sentences.add(sid)

            # Text-level dedup: different sentence_ids can share identical text
            # (e.g., from UNION ALL across group branches or chunk overlaps).
            text_key = (r.get("text") or "")[:100].lower().strip()
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)

            # Build passage: prev + current + next for coherent context
            parts = []
            if r.get("prev_text"):
                parts.append(r["prev_text"].strip())
            parts.append((r.get("text") or "").strip())
            if r.get("next_text"):
                parts.append(r["next_text"].strip())
            passage = " ".join(parts)

            # R6-X: include chunk_text (full parent chunk) alongside the
            # sentence-window passage.  chunk_text is fetched by the Cypher
            # query but was previously discarded.  Synthesis can use it as
            # extended context when the passage alone is insufficient (e.g.
            # date-comparison or entity-count queries where the key fact lives
            # in an adjacent clause rather than the retrieved sentence itself).
            chunk_text = (r.get("chunk_text") or "").strip()
            evidence.append({
                "text": passage,
                "sentence_text": r.get("text") or "",
                "chunk_text": chunk_text,
                "score": r.get("score", 0),
                "document_title": r.get("document_title", "Unknown"),
                "document_id": r.get("document_id", ""),
                "section_path": r.get("section_key") or r.get("section_path", ""),
                "page": r.get("page"),
                "sentence_id": sid,
            })

        logger.info(
            "route6_sentence_search_complete",
            query=query[:50],
            results_raw=len(results),
            evidence_deduped=len(evidence),
            top_scores=[round(e["score"], 4) for e in evidence[:5]],
            top_docs=list(set(e["document_title"] for e in evidence[:10])),
        )

        return evidence

    # ==================================================================
    # R6-XII: Entity-Centric Sentence Expansion
    # ==================================================================

    async def _expand_sentences_via_entities(
        self,
        seed_evidence: List[Dict[str, Any]],
        seed_count: int = 10,
        top_k: int = 20,
        min_overlap: int = 1,
        folder_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Expand sentence pool via shared-entity graph traversal.

        After the initial vector search retrieves seed sentences, this method
        traverses (Sentence)-[:MENTIONS]->(Entity)<-[:MENTIONS]-(Sentence)
        edges to discover additional sentences that share entities with the
        seeds.  This helps multi-hop reasoning where relevant facts live in
        sentences that don't have high vector similarity to the query but
        are topically connected via entities.

        Args:
            seed_evidence: Sentence evidence dicts from vector search (sorted
                by score descending).
            seed_count: Number of top-scoring seeds to use for expansion.
            top_k: Max expanded sentences to return.
            min_overlap: Minimum number of distinct shared entities for a
                sentence to qualify.
            folder_id: Folder scope filter (None = all folders).

        Returns:
            List of evidence dicts matching the schema of
            ``_retrieve_sentence_evidence`` output, with additional fields
            ``expansion_source`` and ``shared_entity_count``.
        """
        if not self.neo4j_driver:
            logger.warning("route6_entity_expansion_no_neo4j_driver")
            return []

        # Use top seed_count sentences as expansion seeds
        seeds = seed_evidence[:seed_count]
        seed_ids = [s["sentence_id"] for s in seeds if s.get("sentence_id")]
        if not seed_ids:
            return []

        # Exclude ALL sentences already in the pool to avoid duplicates
        exclude_ids = [
            s["sentence_id"] for s in seed_evidence if s.get("sentence_id")
        ]

        # Synthetic score: position expanded sentences below genuine vector
        # matches so the reranker controls final ordering.
        seed_scores = [s.get("score", 0) for s in seeds if s.get("score")]
        synthetic_score = min(seed_scores) * 0.8 if seed_scores else 0.3

        group_ids = self.group_ids

        # R6-1: folder scope filter (same pattern as sentence vector search)
        folder_filter_clause = (
            "// R6-1: folder scope filter (no-op when $folder_id IS NULL)\n"
            "        WITH expanded, shared_entity_count, doc, sec,"
            " prev_sent, next_sent\n"
            "        WHERE $folder_id IS NULL OR doc IS NULL"
            " OR EXISTS { MATCH (doc)-[:IN_FOLDER]->(f:Folder)"
            " WHERE f.id = $folder_id AND f.group_id IN $group_ids }\n"
        )

        cypher = f"""
        UNWIND $seed_ids AS seed_id
        MATCH (seed:Sentence {{id: seed_id}})
        WHERE seed.group_id IN $group_ids
        MATCH (seed)-[:MENTIONS]->(e:Entity)
        WHERE e.group_id IN $group_ids
        MATCH (e)<-[:MENTIONS]-(expanded:Sentence)
        WHERE expanded.group_id IN $group_ids
              AND NOT expanded.id IN $exclude_ids

        WITH expanded, count(DISTINCT e) AS shared_entity_count
        WHERE shared_entity_count >= $min_overlap

        OPTIONAL MATCH (expanded)-[:IN_DOCUMENT]->(doc:Document)
        OPTIONAL MATCH (expanded)-[:IN_SECTION]->(sec:Section)
        OPTIONAL MATCH (expanded)-[:NEXT]->(next_sent:Sentence)
        OPTIONAL MATCH (prev_sent:Sentence)-[:NEXT]->(expanded)

        {folder_filter_clause}
        RETURN DISTINCT expanded.id AS sentence_id,
               expanded.text AS text,
               expanded.source AS source,
               expanded.section_path AS section_path,
               sec.path_key AS section_key,
               expanded.page AS page,
               expanded.parent_text AS chunk_text,
               doc.title AS document_title,
               doc.id AS document_id,
               shared_entity_count,
               prev_sent.text AS prev_text,
               next_sent.text AS next_text
        ORDER BY shared_entity_count DESC
        LIMIT $top_k
        """

        try:
            loop = asyncio.get_running_loop()
            driver = self.neo4j_driver

            def _run_expansion():
                with retry_session(driver, read_only=True) as session:
                    records = session.run(
                        cypher,
                        seed_ids=seed_ids,
                        exclude_ids=exclude_ids,
                        group_ids=group_ids,
                        folder_id=folder_id,
                        min_overlap=min_overlap,
                        top_k=top_k,
                    )
                    return [dict(r) for r in records]

            results = await loop.run_in_executor(self._executor, _run_expansion)
        except Exception as e:
            logger.warning("route6_entity_expansion_query_failed", error=str(e))
            return []

        if not results:
            logger.info("route6_entity_expansion_empty",
                        seed_count=len(seed_ids))
            return []

        # Build evidence dicts matching _retrieve_sentence_evidence schema
        evidence: List[Dict[str, Any]] = []
        # Collect seed section paths for proximity boosting
        seed_sections = {s.get("section_path", "") for s in seeds if s.get("section_path")}
        for r in results:
            parts = []
            if r.get("prev_text"):
                parts.append(r["prev_text"].strip())
            parts.append((r.get("text") or "").strip())
            if r.get("next_text"):
                parts.append(r["next_text"].strip())
            passage = " ".join(parts)

            chunk_text = (r.get("chunk_text") or "").strip()
            ev_section = r.get("section_key") or r.get("section_path", "")
            # Section-proximity boost: same section as seeds gets 1.3× score
            ev_score = synthetic_score
            if ev_section and ev_section in seed_sections:
                ev_score = synthetic_score * 1.3
            evidence.append({
                "text": passage,
                "sentence_text": r.get("text") or "",
                "chunk_text": chunk_text,
                "score": ev_score,
                "document_title": r.get("document_title", "Unknown"),
                "document_id": r.get("document_id", ""),
                "section_path": ev_section,
                "page": r.get("page"),
                "sentence_id": r.get("sentence_id", ""),
                "expansion_source": "entity",
                "shared_entity_count": r.get("shared_entity_count", 0),
            })

        logger.info(
            "route6_entity_expansion_complete",
            seed_count=len(seed_ids),
            expanded=len(evidence),
            top_overlap=[e["shared_entity_count"] for e in evidence[:5]],
            top_docs=list(set(e["document_title"] for e in evidence[:10])),
        )

        return evidence

    # ==================================================================
    # Section Heading Search (via structural_embedding, Route 5 Tier 2)
    # ==================================================================

    async def _retrieve_section_headings(
        self,
        query: str,
        top_k: int = 10,
        folder_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve section headings via structural embedding cosine similarity.

        Uses the same Section.structural_embedding (Voyage 2048d) that Route 5
        Tier 2 uses.  This surfaces document structure like section titles
        ("EXHIBIT A - SCOPE OF WORK") that sentence search misses because
        headings are sparse text without sentence structure.

        Args:
            query: User query to embed and match against section headings.
            top_k: Max sections to retrieve.
            folder_id: Folder scope filter (None = all folders).

        Returns:
            List of section dicts with title, summary, path_key, document_title, score.
        """
        voyage_service = _get_voyage_service()
        if not voyage_service:
            logger.warning("route6_section_search_no_voyage_service")
            return []

        if not self.neo4j_driver:
            logger.warning("route6_section_search_no_neo4j_driver")
            return []

        # 1. Embed query with Voyage (sync HTTP call — run off event loop)
        try:
            loop = asyncio.get_running_loop()
            query_embedding = await loop.run_in_executor(
                self._executor, voyage_service.embed_query, query,
            )
        except Exception as e:
            logger.warning("route6_section_embed_failed", error=str(e))
            return []

        min_similarity = float(os.getenv("ROUTE6_SECTION_MIN_SIMILARITY", "0.25"))
        group_ids = self.group_ids

        # 2. Cosine similarity against Section.structural_embedding
        # Note: no vector index exists for Section.structural_embedding (architectural
        # decision — see ARCHITECTURE_ROUTE5_UNIFIED_HIPPORAG_2026-02-16.md §section).
        # Brute-force scan is acceptable: typically <20 sections per group.
        cypher = """
        MATCH (s:Section)
        WHERE s.group_id IN $group_ids AND s.structural_embedding IS NOT NULL
        WITH s, vector.similarity.cosine(s.structural_embedding, $query_embedding) AS score
        WHERE score >= $min_similarity

        // Get parent document title
        OPTIONAL MATCH (s)<-[:HAS_SECTION]-(doc:Document)

        // R6-2: Folder scope filter (no-op when $folder_id IS NULL)
        WITH s, score, doc
        WHERE $folder_id IS NULL OR doc IS NULL
           OR EXISTS { MATCH (doc)-[:IN_FOLDER]->(f:Folder)
                       WHERE f.id = $folder_id AND f.group_id IN $group_ids }

        RETURN s.title AS title,
               s.summary AS summary,
               s.path_key AS path_key,
               s.depth AS depth,
               doc.title AS document_title,
               score
        ORDER BY score DESC
        LIMIT $top_k
        """

        try:
            loop = asyncio.get_running_loop()
            driver = self.neo4j_driver

            def _run_search():
                with retry_session(driver, read_only=True) as session:
                    records = session.run(
                        cypher,
                        query_embedding=query_embedding,
                        group_ids=group_ids,
                        min_similarity=min_similarity,
                        top_k=top_k,
                        folder_id=folder_id,
                    )
                    return [dict(r) for r in records]

            results = await loop.run_in_executor(self._executor, _run_search)
        except Exception as e:
            logger.warning("route6_section_search_failed", error=str(e))
            return []

        if not results:
            logger.info("route6_section_search_empty", query=query[:50])
            return []

        logger.info(
            "route6_section_search_complete",
            query=query[:50],
            matched=len(results),
            top_sections=[
                (r.get("title", "?")[:40], round(r.get("score", 0), 4))
                for r in results[:5]
            ],
        )

        return results

    # ==================================================================
    # Document diversification (reused from Route 3)
    # ==================================================================

    @staticmethod
    def _diversify_by_document(
        evidence: List[Dict[str, Any]],
        top_k: int,
        min_per_doc: int = 2,
        score_gate: float = 0.85,
    ) -> List[Dict[str, Any]]:
        """Ensure every document with relevant sentences gets representation.

        Algorithm:
          1. Group sentences by document_id (preserving score order).
          2. Score-gate: only reserve from a minority document if its
             top sentence scores >= score_gate x top-1 global score.
          3. Reserve the top min_per_doc sentences from each qualifying doc.
          4. Fill remaining slots with globally highest-scoring sentences.
          5. Sort final list by score descending.
        """
        by_doc: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for ev in evidence:
            doc_id = ev.get("document_id") or ev.get("document_title") or "unknown"
            by_doc[doc_id].append(ev)

        top_score = evidence[0].get("score", 0) if evidence else 0
        score_floor = top_score * score_gate

        selected_ids: set = set()
        selected: List[Dict[str, Any]] = []

        # Phase 1: reserve min_per_doc from each qualifying document
        for doc_id, doc_evidence in by_doc.items():
            best_doc_score = doc_evidence[0].get("score", 0) if doc_evidence else 0
            if best_doc_score < score_floor:
                continue
            for ev in doc_evidence[:min_per_doc]:
                sid = ev.get("sentence_id", id(ev))
                if sid not in selected_ids:
                    selected_ids.add(sid)
                    selected.append(ev)

        # Phase 2: fill remaining slots
        remaining = top_k - len(selected)
        if remaining > 0:
            for ev in evidence:
                sid = ev.get("sentence_id", id(ev))
                if sid not in selected_ids:
                    selected_ids.add(sid)
                    selected.append(ev)
                    remaining -= 1
                    if remaining <= 0:
                        break

        selected.sort(key=lambda e: e.get("score", 0), reverse=True)

        logger.info(
            "route6_sentence_diversity_applied",
            pool_size=len(evidence),
            selected=len(selected),
            top_k=top_k,
        )

        return selected[:top_k]

    # ==================================================================
    # Denoise + Rerank (reused from Route 3)
    # ==================================================================

    @staticmethod
    def _denoise_sentences(
        evidence: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Remove noisy, non-informative sentences before reranking.

        Filters out HTML fragments, signature blocks, tiny fragments,
        and bare headings without sentence punctuation.
        """
        cleaned: List[Dict[str, Any]] = []

        for ev in evidence:
            text = (ev.get("sentence_text") or ev.get("text") or "").strip()
            passage = (ev.get("text") or "").strip()

            # Rule 1: HTML / markup-heavy
            tag_count = len(re.findall(r"<[^>]+>", text))
            if tag_count >= 2:
                continue

            # Rule 2: Too short / fragment
            if len(text) < 25:
                continue

            # Rule 3: Signature / form boilerplate
            if re.search(
                r"(?i)(signature|signed this|print\)|registration number"
                r"|authorized representative)",
                text,
            ):
                continue

            # Rule 4: Bare label ending with colon
            if len(text) < 60 and text.endswith(":"):
                continue

            # Rule 5: No sentence structure (heading-only)
            if len(text) < 50 and not re.search(r"[.?!]", text):
                continue

            # Strip residual HTML tags from the passage
            if "<" in passage:
                passage = re.sub(r"<[^>]+>", "", passage).strip()
                ev = {**ev, "text": passage}

            cleaned.append(ev)

        logger.info(
            "route6_denoise_sentences",
            before=len(evidence),
            after=len(cleaned),
            removed=len(evidence) - len(cleaned),
        )
        return cleaned

    async def _rerank_sentences(
        self,
        query: str,
        evidence: List[Dict[str, Any]],
        top_k: int = 15,
    ) -> List[Dict[str, Any]]:
        """Rerank denoised sentences using voyage-rerank-2.5."""
        rerank_model = os.getenv("ROUTE6_RERANK_MODEL", "rerank-2.5")

        try:
            vc = make_voyage_client()
            documents = [ev.get("sentence_text") or ev.get("text") or "" for ev in evidence]

            rr_result = await rerank_with_retry(
                vc,
                query=query,
                documents=documents,
                model=rerank_model,
                top_k=min(top_k, len(documents)),
                executor=self._executor,
            )

            # Track reranker usage (fire-and-forget)
            try:
                _rerank_tokens = getattr(rr_result, "total_tokens", 0)
                acc = getattr(self, "_token_accumulator", None)
                if acc is not None:
                    acc.add_rerank(rerank_model, _rerank_tokens, len(documents))
                from src.core.services.usage_tracker import get_usage_tracker
                _tracker = get_usage_tracker()
                asyncio.ensure_future(_tracker.log_rerank_usage(
                    partition_id=self.group_id,
                    model=rerank_model,
                    total_tokens=_rerank_tokens,
                    documents_reranked=len(documents),
                    route="route_6",
                    user_id=None,
                ))
            except Exception:
                pass

            reranked: List[Dict[str, Any]] = []
            for rr in rr_result.results:
                # R6-4: Propagate reranker relevance score to the canonical `score`
                # field so that downstream consumers (citations, diversity) see the
                # reranked score instead of the original embedding similarity score.
                ev = {
                    **evidence[rr.index],
                    "rerank_score": rr.relevance_score,
                    "score": rr.relevance_score,
                }
                reranked.append(ev)

            logger.info(
                "route6_rerank_complete",
                model=rerank_model,
                input_count=len(evidence),
                output_count=len(reranked),
                top_score=round(reranked[0]["rerank_score"], 4) if reranked else 0,
                bottom_score=round(reranked[-1]["rerank_score"], 4) if reranked else 0,
            )
            return reranked

        except Exception as e:
            # R6-3: Reranker failures must not crash the request.  The caller in
            # execute() also wraps this call, but the explicit return here ensures
            # graceful degradation even when called from other contexts.
            logger.warning("route6_rerank_failed", error=str(e))
            return evidence[:top_k]

    # ==================================================================
    # Citations
    # ==================================================================

    @staticmethod
    def _build_citations(
        communities: List[Dict[str, Any]],
        scores: List[float],
        sentence_evidence: List[Dict[str, Any]],
    ) -> List[Citation]:
        """Build citations from communities and sentence evidence.

        Community citations come first (thematic sources), followed by
        sentence-level citations (direct document evidence).
        """
        citations: List[Citation] = []

        # Community-level citations (all matched communities, not just those with claims)
        for i, (community, score) in enumerate(zip(communities, scores), 1):
            title = community.get("title", "Untitled")
            summary = community.get("summary", "")
            if summary.strip():
                citations.append(
                    Citation(
                        index=i,
                        sentence_id=f"community_{community.get('id', i)}",
                        document_id="",
                        document_title=title,
                        score=round(score, 4),
                        text_preview=summary[:200],
                    )
                )

        # Sentence-level citations (top 5 documents to avoid overload)
        offset = len(citations)
        seen_docs: set = set()
        for ev in sentence_evidence:
            doc_id = ev.get("document_id", "")
            doc_title = ev.get("document_title", "Unknown")
            dedup_key = doc_id or doc_title
            if dedup_key in seen_docs:
                continue
            seen_docs.add(dedup_key)
            offset += 1
            sent_text = ev.get("sentence_text", "")
            citations.append(
                Citation(
                    index=offset,
                    sentence_id=ev.get("sentence_id", f"sentence_{offset}"),
                    document_id=ev.get("document_id", ""),
                    document_title=doc_title,
                    score=round(ev.get("score", 0), 4),
                    text_preview=sent_text[:200],
                    page_number=ev.get("page"),
                    section_path=ev.get("section_path", ""),
                    sentence_text=sent_text,
                    sentence_length=len(sent_text),
                )
            )
            if len(seen_docs) >= 5:
                break

        return citations
