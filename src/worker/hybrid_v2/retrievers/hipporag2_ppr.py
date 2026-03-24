"""True Personalized PageRank with Passage Nodes for HippoRAG 2.

Implements the core HippoRAG 2 graph architecture where PPR operates on
a unified graph containing BOTH entity nodes AND passage (Sentence) nodes.

Key differences from the existing hipporag_retriever.py PPR:

1. **Passage nodes in graph**: Sentence nodes are first-class graph nodes,
   connected to entities via MENTIONS edges. PPR probability mass flows
   Entity <-> Passage, so passage scores come directly from the random walk.

2. **Weighted edges**: Edge weights are used in rank distribution. MENTIONS
   edges get a configurable passage_node_weight (default 0.05) to balance
   entity vs. passage influence. SEMANTICALLY_SIMILAR edges use their
   stored cosine similarity score.

3. **Undirected graph**: All edges are bidirectional (matching upstream
   HippoRAG 2 which uses igraph with directed=False).

4. **Damping = 0.5**: Upstream default (vs our existing 0.85).

5. **Dual output**: Returns both passage scores (document rankings) and
   entity scores (for synthesis evidence_nodes).

Reference: HippoRAG 2 (ICML '25) — https://arxiv.org/abs/2502.14802
"""

from __future__ import annotations

import asyncio
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import structlog

from ..services.neo4j_retry import retry_session

logger = structlog.get_logger(__name__)


class HippoRAG2PPR:
    """True in-memory PPR with passage nodes.

    Graph structure:
        Nodes: Entity nodes + Sentence (passage) nodes
        Edges (undirected, weighted):
            - Entity <-> Entity via RELATED_TO (weight = r.weight, default 1.0)
            - Entity <-> Passage via MENTIONS (weight = 1.0, matching upstream)
            - Entity <-> Entity via SEMANTICALLY_SIMILAR (weight = similarity)

    Seed vector:
        - Entity seeds: from triple linking (query-to-triple matching)
        - Passage seeds: from DPR retrieval (score * passage_node_weight)

    Output:
        - passage_scores: ranked Sentence IDs (= document/chunk rankings)
        - entity_scores: ranked entity names (for synthesis evidence_nodes)
    """

    def __init__(self) -> None:
        self._node_to_idx: Dict[str, int] = {}  # node_id -> index
        self._idx_to_node: Dict[int, str] = {}  # index -> node_id
        self._node_types: Dict[int, str] = {}  # index -> "entity"|"passage"
        self._node_names: Dict[int, str] = {}  # index -> display name
        self._passage_full_texts: Dict[str, str] = {}  # node_id -> full text (for reranker)
        self._passage_embeddings: Dict[str, List[float]] = {}  # node_id -> embedding vector (for pre-filter)
        self._entity_mention_counts: Dict[str, int] = {}  # entity_id -> # passages mentioning it
        # Community metadata for community-balanced personalization
        self._community_id: Dict[int, int] = {}  # node_idx -> community_id
        self._community_sizes: Dict[int, int] = {}  # community_id -> member_count
        # Weighted adjacency: source_idx -> [(target_idx, weight)]
        self._adj: Dict[int, List[Tuple[int, float]]] = {}
        # Precomputed sum of outgoing weights per node (for rank distribution)
        self._out_weight_sum: Dict[int, float] = {}
        self._loaded = False
        self._node_count = 0

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def node_count(self) -> int:
        return self._node_count

    def get_all_passage_texts(self) -> Dict[str, str]:
        """Return all passage (Sentence) node IDs mapped to their full text.

        Used by the cross-encoder reranker to avoid a separate Neo4j fetch.
        """
        return self._passage_full_texts

    def get_all_passage_embeddings(self) -> Dict[str, List[float]]:
        """Return all passage node IDs mapped to their embedding vectors.

        Used for fast cosine pre-filtering before cross-encoder reranking.
        """
        return self._passage_embeddings

    def cosine_prefilter(
        self,
        query_embedding: List[float],
        top_k: int = 100,
        candidate_ids: Optional[List[str]] = None,
    ) -> List[Tuple[str, float]]:
        """Fast in-memory cosine similarity pre-filter for passages.

        Uses cached passage embeddings (loaded at graph init) to rank
        passages by cosine similarity to the query embedding. This avoids
        a Neo4j roundtrip and can reduce cross-encoder reranker input
        from N to top_k, cutting reranker token usage proportionally.

        Args:
            query_embedding: Query vector (same dim as passage embeddings).
            top_k: Number of top passages to return.
            candidate_ids: If provided, only score these IDs (skip others).

        Returns:
            List of (sentence_id, cosine_similarity) sorted best-first.
        """
        import numpy as np

        if not self._passage_embeddings:
            return []

        q = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q = q / q_norm

        if candidate_ids is not None:
            ids = [sid for sid in candidate_ids if sid in self._passage_embeddings]
        else:
            ids = list(self._passage_embeddings.keys())

        if not ids:
            return []

        # Build matrix and compute cosine in one vectorized operation
        mat = np.array([self._passage_embeddings[sid] for sid in ids], dtype=np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-10)
        mat = mat / norms
        scores = mat @ q  # cosine similarities

        # Get top-k indices
        k = min(top_k, len(ids))
        top_indices = np.argpartition(scores, -k)[-k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        return [(ids[i], float(scores[i])) for i in top_indices]

    @property
    def entity_mention_counts(self) -> Dict[str, int]:
        """entity_id -> number of passages mentioning it (IDF denominator)."""
        return self._entity_mention_counts

    def compute_entity_bridge_scores(
        self,
        passage_ids: List[str],
        seed_entity_ids: Set[str],
    ) -> Dict[str, float]:
        """Compute structural relevance for passages based on entity overlap with query seeds.

        For each passage, finds its directly connected entities in the graph,
        checks which ones overlap with the query seed entities, and weights
        by entity IDF (1/log(1 + mention_count)) so rare/specific entities
        contribute more than hub entities.

        Returns: {passage_id: bridge_score} — higher = more structurally relevant.
        """
        import math
        seed_idx_set = {self._node_to_idx[eid] for eid in seed_entity_ids
                        if eid in self._node_to_idx}
        if not seed_idx_set:
            return {pid: 0.0 for pid in passage_ids}

        result: Dict[str, float] = {}
        for pid in passage_ids:
            pidx = self._node_to_idx.get(pid)
            if pidx is None:
                result[pid] = 0.0
                continue
            score = 0.0
            for neighbor_idx, _weight in self._adj.get(pidx, []):
                if neighbor_idx in seed_idx_set and self._node_types.get(neighbor_idx) == "entity":
                    eid = self._idx_to_node[neighbor_idx]
                    mc = max(self._entity_mention_counts.get(eid, 1), 1)
                    score += 1.0 / math.log(1.0 + mc)
            result[pid] = score
        return result

    def _add_node(self, node_id: str, node_type: str, name: str) -> int:
        """Add a node to the graph, return its index."""
        if node_id in self._node_to_idx:
            return self._node_to_idx[node_id]
        idx = self._node_count
        self._node_to_idx[node_id] = idx
        self._idx_to_node[idx] = node_id
        self._node_types[idx] = node_type
        self._node_names[idx] = name
        self._adj[idx] = []
        self._node_count += 1
        return idx

    def _add_edge(self, src_idx: int, tgt_idx: int, weight: float) -> None:
        """Add a weighted undirected edge (both directions)."""
        self._adj[src_idx].append((tgt_idx, weight))
        self._adj[tgt_idx].append((src_idx, weight))

    def _apply_mentions_idf(self, mode: str) -> None:
        """Reweight Sentence↔Entity (MENTIONS) edges by inverse entity degree.

        Hub entities like "owner" (deg=41) get their edge weights reduced
        relative to rare entities (deg=1), dampening hub-driven noise in
        PPR/APPNP propagation — the Article Rank principle applied to our
        bipartite passage-entity graph.
        """
        import math as _math

        # Compute weight factor per entity node
        entity_factors: Dict[int, float] = {}
        for eid, degree in self._entity_mention_counts.items():
            idx = self._node_to_idx.get(eid)
            if idx is None:
                continue
            if mode == "log":
                entity_factors[idx] = 1.0 / _math.log(1 + degree)
            elif mode == "sqrt":
                entity_factors[idx] = 1.0 / _math.sqrt(degree)
            elif mode == "inv":
                entity_factors[idx] = 1.0 / degree
            else:
                entity_factors[idx] = 1.0

        if not entity_factors:
            return

        # Rebuild adjacency lists with reweighted MENTIONS edges.
        # MENTIONS edges connect passage↔entity nodes. We identify them
        # by checking if exactly one endpoint is an entity node.
        reweighted = 0
        for src_idx in range(self._node_count):
            new_edges = []
            for tgt_idx, w in self._adj.get(src_idx, []):
                # Check if this edge connects to an entity with a factor
                if src_idx in entity_factors:
                    new_edges.append((tgt_idx, w * entity_factors[src_idx]))
                    reweighted += 1
                elif tgt_idx in entity_factors:
                    new_edges.append((tgt_idx, w * entity_factors[tgt_idx]))
                    reweighted += 1
                else:
                    new_edges.append((tgt_idx, w))
            self._adj[src_idx] = new_edges

        logger.info(
            "mentions_idf_reweighting",
            mode=mode,
            entities_reweighted=len(entity_factors),
            edges_reweighted=reweighted,
        )

    def _finalize_graph(self) -> None:
        """Precompute outgoing weight sums and community sizes."""
        for idx in range(self._node_count):
            edges = self._adj.get(idx, [])
            self._out_weight_sum[idx] = sum(w for _, w in edges) if edges else 0.0

        # Compute community sizes from loaded community_id metadata
        self._community_sizes.clear()
        for idx, cid in self._community_id.items():
            self._community_sizes[cid] = self._community_sizes.get(cid, 0) + 1

    async def load_graph(
        self,
        neo4j_driver: Any,
        group_ids: List[str],
        passage_node_weight: float = 0.05,
        synonym_threshold: float = 0.70,
        include_section_graph: bool = False,
        section_edge_weight: float = 0.1,
        section_sim_threshold: float = 0.5,
        include_appears_in_section: bool = False,
        include_next_in_section: bool = False,
        mentions_idf_weighting: str = "none",
    ) -> None:
        """Load Entity + Sentence nodes and edges from Neo4j.

        Args:
            neo4j_driver: Sync Neo4j driver instance.
            group_ids: Multi-tenant group IDs to load into a single graph.
            passage_node_weight: Weight for MENTIONS edges (default 0.05).
            synonym_threshold: Min similarity for SEMANTICALLY_SIMILAR entity
                edges (default 0.8, matching upstream HippoRAG 2).
            include_section_graph: Phase 2 — also load Section nodes and edges.
            section_edge_weight: Weight for IN_SECTION edges (default 0.1).
            section_sim_threshold: Min similarity for section SEMANTICALLY_SIMILAR
                edges (default 0.5).
            include_appears_in_section: Load Entity→Section APPEARS_IN_SECTION
                edges as shortcuts (bypasses Sentence→Section hop).
            include_next_in_section: Load Sentence→Sentence NEXT_IN_SECTION
                edges for sequential sentence bridging.
            mentions_idf_weighting: Reweight MENTIONS edges by inverse entity
                degree to dampen hub entities (Article Rank principle).
                "none" = flat weight 1.0 (default, upstream HippoRAG 2).
                "log"  = weight = 1 / log(1 + degree).
                "sqrt" = weight = 1 / sqrt(degree).
                "inv"  = weight = 1 / degree (full Article Rank style).
        """
        t0 = time.perf_counter()

        await asyncio.to_thread(
            self._load_graph_sync,
            neo4j_driver,
            group_ids,
            passage_node_weight,
            synonym_threshold,
            include_section_graph,
            section_edge_weight,
            section_sim_threshold,
            include_appears_in_section,
            include_next_in_section,
        )

        # Reweight MENTIONS edges by inverse entity degree (hub dampening).
        if mentions_idf_weighting != "none":
            self._apply_mentions_idf(mentions_idf_weighting)

        self._finalize_graph()
        self._loaded = True

        entity_count = sum(
            1 for t in self._node_types.values() if t == "entity"
        )
        passage_count = sum(
            1 for t in self._node_types.values() if t == "passage"
        )
        section_count = sum(
            1 for t in self._node_types.values() if t == "section"
        )
        edge_count = sum(len(edges) for edges in self._adj.values()) // 2

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.info(
            "hipporag2_ppr_graph_loaded",
            group_ids=group_ids,
            total_nodes=self._node_count,
            entity_nodes=entity_count,
            passage_nodes=passage_count,
            section_nodes=section_count,
            edges=edge_count,
            elapsed_ms=elapsed_ms,
        )

    def _load_graph_sync(
        self,
        neo4j_driver: Any,
        group_ids: List[str],
        passage_node_weight: float,
        synonym_threshold: float,
        include_section_graph: bool,
        section_edge_weight: float,
        section_sim_threshold: float,
        include_appears_in_section: bool = False,
        include_next_in_section: bool = False,
    ) -> None:
        """Synchronous graph loading from Neo4j."""
        entity_edge_count = 0
        mentions_edge_count = 0
        synonym_edge_count = 0
        # Bug 11 fix: deduplicate undirected edges.
        # _add_edge adds both A→B and B→A. If Neo4j stores both directions of a
        # RELATED_TO/SEMANTICALLY_SIMILAR edge (common with MERGE-based ingestion),
        # calling _add_edge twice creates 4 adjacency entries instead of 2 and
        # doubles edge weight in PPR. Track canonical (min_idx, max_idx) pairs.
        seen_entity_edges: set = set()
        seen_synonym_edges: set = set()

        with retry_session(neo4j_driver) as session:
            # ----------------------------------------------------------
            # 1. Load Entity nodes (with community_id for balanced seeds)
            # ----------------------------------------------------------
            result = session.run(
                "MATCH (e:Entity) "
                "WHERE e.group_id IN $group_ids "
                "RETURN e.id AS id, e.name AS name, "
                "e.community_id AS community_id",
                group_ids=group_ids,
            )
            for record in result:
                idx = self._add_node(record["id"], "entity", record["name"] or "")
                cid = record["community_id"]
                if cid is not None:
                    self._community_id[idx] = int(cid)

            # ----------------------------------------------------------
            # 2. Load Sentence (passage) nodes + embeddings
            # ----------------------------------------------------------
            result = session.run(
                "MATCH (c:Sentence) "
                "WHERE c.group_id IN $group_ids "
                "RETURN c.id AS id, c.text AS text, "
                "c.sentence_embedding AS emb",
                group_ids=group_ids,
            )
            for record in result:
                # Use first 80 chars of text as display name
                full_text = record["text"] or ""
                self._add_node(record["id"], "passage", full_text[:80])
                self._passage_full_texts[record["id"]] = full_text
                emb = record["emb"]
                if emb is not None:
                    self._passage_embeddings[record["id"]] = list(emb)

            # ----------------------------------------------------------
            # 3. Entity-Entity edges via RELATED_TO
            # ----------------------------------------------------------
            result = session.run(
                "MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity) "
                "WHERE e1.group_id IN $group_ids "
                "AND e2.group_id IN $group_ids "
                "RETURN e1.id AS src, e2.id AS tgt, "
                "coalesce(r.weight, 1.0) AS weight",
                group_ids=group_ids,
            )
            for record in result:
                src_idx = self._node_to_idx.get(record["src"])
                tgt_idx = self._node_to_idx.get(record["tgt"])
                if src_idx is not None and tgt_idx is not None:
                    edge_key = (min(src_idx, tgt_idx), max(src_idx, tgt_idx))
                    if edge_key not in seen_entity_edges:
                        seen_entity_edges.add(edge_key)
                        self._add_edge(src_idx, tgt_idx, float(record["weight"]))
                        entity_edge_count += 1

            # ----------------------------------------------------------
            # 4. Passage-Entity edges via MENTIONS
            #    Upstream HippoRAG 2 uses weight=1.0 for passage-entity
            #    graph edges (passage_node_weight is only for PPR seeding).
            # ----------------------------------------------------------
            result = session.run(
                "MATCH (c:Sentence)-[:MENTIONS]->(e:Entity) "
                "WHERE c.group_id IN $group_ids "
                "AND e.group_id IN $group_ids "
                "RETURN c.id AS sentence_id, e.id AS entity_id",
                group_ids=group_ids,
            )
            for record in result:
                src_idx = self._node_to_idx.get(record["sentence_id"])
                tgt_idx = self._node_to_idx.get(record["entity_id"])
                if src_idx is not None and tgt_idx is not None:
                    self._add_edge(src_idx, tgt_idx, 1.0)
                    mentions_edge_count += 1
                    eid = record["entity_id"]
                    self._entity_mention_counts[eid] = self._entity_mention_counts.get(eid, 0) + 1

            # ----------------------------------------------------------
            # 5. Entity-Entity synonym edges via SEMANTICALLY_SIMILAR
            #    Re-enabled: entity synonymy provides critical cross-doc
            #    bridges (upstream HippoRAG 2 uses topk=2047 @0.8).
            #    Our entity dedup at 0.8 merges identical entities, so
            #    synonymy edges at lower thresholds connect semantically
            #    related but distinct entities across documents.
            # ----------------------------------------------------------
            result = session.run(
                "MATCH (e1:Entity)-[r:SEMANTICALLY_SIMILAR]->(e2:Entity) "
                "WHERE e1.group_id IN $group_ids "
                "AND e2.group_id IN $group_ids "
                "AND r.similarity >= $threshold "
                "RETURN e1.id AS src, e2.id AS tgt, "
                "r.similarity AS weight",
                group_ids=group_ids,
                threshold=synonym_threshold,
            )
            for record in result:
                src_idx = self._node_to_idx.get(record["src"])
                tgt_idx = self._node_to_idx.get(record["tgt"])
                if src_idx is not None and tgt_idx is not None:
                    edge_key = (min(src_idx, tgt_idx), max(src_idx, tgt_idx))
                    if edge_key not in seen_synonym_edges:
                        seen_synonym_edges.add(edge_key)
                        self._add_edge(src_idx, tgt_idx, float(record["weight"]))
                        synonym_edge_count += 1

            # ----------------------------------------------------------
            # 5b. Sentence-Sentence edges via SEMANTICALLY_SIMILAR
            #     Created by step 4.2 sentence KNN — enables cross-document
            #     PPR traversal between similar sentences.
            # ----------------------------------------------------------
            seen_sentence_edges: set = set()
            sentence_sim_count = 0
            result = session.run(
                "MATCH (s1:Sentence)-[r:SEMANTICALLY_SIMILAR]->(s2:Sentence) "
                "WHERE s1.group_id IN $group_ids "
                "AND s2.group_id IN $group_ids "
                "AND r.similarity >= $threshold "
                "RETURN s1.id AS src, s2.id AS tgt, "
                "r.similarity AS weight",
                group_ids=group_ids,
                threshold=synonym_threshold,
            )
            for record in result:
                src_idx = self._node_to_idx.get(record["src"])
                tgt_idx = self._node_to_idx.get(record["tgt"])
                if src_idx is not None and tgt_idx is not None:
                    edge_key = (min(src_idx, tgt_idx), max(src_idx, tgt_idx))
                    if edge_key not in seen_sentence_edges:
                        seen_sentence_edges.add(edge_key)
                        self._add_edge(src_idx, tgt_idx, float(record["weight"]))
                        sentence_sim_count += 1

            # ----------------------------------------------------------
            # 6. Phase 2: Section graph (optional)
            # ----------------------------------------------------------
            if include_section_graph:
                self._load_section_graph_sync(
                    session, group_ids, section_edge_weight, section_sim_threshold
                )

            # ----------------------------------------------------------
            # 7. APPEARS_IN_SECTION: Entity→Section shortcut (optional)
            #    Bypasses the Sentence→IN_SECTION→Section path, giving
            #    entities direct access to sections for cross-doc bridging.
            # ----------------------------------------------------------
            appears_in_section_count = 0
            if include_appears_in_section and include_section_graph:
                result = session.run(
                    "MATCH (e:Entity)-[:APPEARS_IN_SECTION]->(s:Section) "
                    "WHERE e.group_id IN $group_ids "
                    "AND s.group_id IN $group_ids "
                    "RETURN e.id AS entity_id, s.id AS section_id",
                    group_ids=group_ids,
                )
                for record in result:
                    src_idx = self._node_to_idx.get(record["entity_id"])
                    tgt_idx = self._node_to_idx.get(record["section_id"])
                    if src_idx is not None and tgt_idx is not None:
                        self._add_edge(src_idx, tgt_idx, section_edge_weight)
                        appears_in_section_count += 1

            # ----------------------------------------------------------
            # 8. NEXT_IN_SECTION: sequential sentence links (optional)
            #    Connects consecutive sentences within sections so PPR
            #    can walk from a found sentence to its neighbors.
            # ----------------------------------------------------------
            next_in_section_count = 0
            if include_next_in_section:
                result = session.run(
                    "MATCH (s1:Sentence)-[:NEXT_IN_SECTION]->(s2:Sentence) "
                    "WHERE s1.group_id IN $group_ids "
                    "AND s2.group_id IN $group_ids "
                    "RETURN s1.id AS src, s2.id AS tgt",
                    group_ids=group_ids,
                )
                for record in result:
                    src_idx = self._node_to_idx.get(record["src"])
                    tgt_idx = self._node_to_idx.get(record["tgt"])
                    if src_idx is not None and tgt_idx is not None:
                        self._add_edge(src_idx, tgt_idx, section_edge_weight)
                        next_in_section_count += 1

        logger.debug(
            "hipporag2_ppr_edges_loaded",
            entity_edges=entity_edge_count,
            mentions_edges=mentions_edge_count,
            synonym_edges=synonym_edge_count,
            sentence_sim_edges=sentence_sim_count,
            appears_in_section_edges=appears_in_section_count if include_appears_in_section else 0,
            next_in_section_edges=next_in_section_count if include_next_in_section else 0,
        )

    def _load_section_graph_sync(
        self,
        session: Any,
        group_ids: List[str],
        section_edge_weight: float,
        section_sim_threshold: float,
    ) -> None:
        """Load Section nodes and edges for Phase 2 augmentation."""
        # Section nodes — include section_ordinal for ordinal-weighted edges
        # Also load section_embedding so neural teleportation can seed
        # sections via cosine similarity (e.g. query "hold harmless" matches
        # section title "HOLD HARMLESS", mass then flows to child sentences).
        result = session.run(
            "MATCH (s:Section) "
            "WHERE s.group_id IN $group_ids "
            "RETURN s.id AS id, s.title AS title, "
            "s.section_ordinal AS ordinal, s.section_embedding AS emb",
            group_ids=group_ids,
        )
        section_ordinals: Dict[str, int] = {}
        section_emb_count = 0
        for record in result:
            self._add_node(record["id"], "section", record["title"] or "")
            if record["ordinal"] is not None:
                section_ordinals[record["id"]] = record["ordinal"]
            emb = record["emb"]
            if emb is not None:
                self._passage_embeddings[record["id"]] = list(emb)
                section_emb_count += 1
        if section_emb_count > 0:
            logger.info(
                "section_embeddings_loaded_for_neural_teleportation",
                section_count=section_emb_count,
            )

        # Passage <-> Section via IN_SECTION
        result = session.run(
            "MATCH (c:Sentence)-[:IN_SECTION]->(s:Section) "
            "WHERE c.group_id IN $group_ids "
            "AND s.group_id IN $group_ids "
            "RETURN c.id AS sentence_id, s.id AS section_id",
            group_ids=group_ids,
        )
        for record in result:
            src_idx = self._node_to_idx.get(record["sentence_id"])
            tgt_idx = self._node_to_idx.get(record["section_id"])
            if src_idx is not None and tgt_idx is not None:
                self._add_edge(src_idx, tgt_idx, section_edge_weight)

        # Section <-> Section via SEMANTICALLY_SIMILAR — ordinal-weighted
        # Bug 14 fix: deduplicate undirected edges (same pattern as entity edges).
        seen_section_sim_edges: set = set()
        result = session.run(
            "MATCH (s1:Section)-[sim:SEMANTICALLY_SIMILAR]->(s2:Section) "
            "WHERE s1.group_id IN $group_ids "
            "AND s2.group_id IN $group_ids "
            "AND sim.similarity >= $threshold "
            "RETURN s1.id AS src, s2.id AS tgt, "
            "sim.similarity AS weight",
            group_ids=group_ids,
            threshold=section_sim_threshold,
        )
        for record in result:
            src_idx = self._node_to_idx.get(record["src"])
            tgt_idx = self._node_to_idx.get(record["tgt"])
            if src_idx is not None and tgt_idx is not None:
                edge_key = (min(src_idx, tgt_idx), max(src_idx, tgt_idx))
                if edge_key not in seen_section_sim_edges:
                    seen_section_sim_edges.add(edge_key)
                    base_weight = float(record["weight"])
                    # Decay by ordinal distance (closer siblings = higher weight)
                    src_ord = section_ordinals.get(record["src"], 0)
                    tgt_ord = section_ordinals.get(record["tgt"], 0)
                    ordinal_distance = abs(src_ord - tgt_ord)
                    decay = 1.0 / (1.0 + ordinal_distance * 0.2)
                    self._add_edge(src_idx, tgt_idx, base_weight * decay)

        # Section <-> Section via SHARES_ENTITY — cross-document bridge.
        # Sections sharing entities across documents form thematic bridges
        # that PPR can traverse to reach sentences in related sections.
        shares_entity_count = 0
        result = session.run(
            "MATCH (s1:Section)-[r:SHARES_ENTITY]->(s2:Section) "
            "WHERE s1.group_id IN $group_ids "
            "AND s2.group_id IN $group_ids "
            "RETURN s1.id AS src, s2.id AS tgt, "
            "r.shared_count AS shared_count",
            group_ids=group_ids,
        )
        for record in result:
            src_idx = self._node_to_idx.get(record["src"])
            tgt_idx = self._node_to_idx.get(record["tgt"])
            if src_idx is not None and tgt_idx is not None:
                edge_key = (min(src_idx, tgt_idx), max(src_idx, tgt_idx))
                if edge_key not in seen_section_sim_edges:
                    seen_section_sim_edges.add(edge_key)
                    # Weight proportional to shared entity count, capped
                    shared = record["shared_count"] or 1
                    weight = min(shared * 0.05, section_edge_weight)
                    self._add_edge(src_idx, tgt_idx, weight)
                    shares_entity_count += 1

    def run_ppr(
        self,
        entity_seeds: Dict[str, float],
        passage_seeds: Dict[str, float],
        damping: float = 0.5,
        max_iterations: int = 50,
        convergence_threshold: float = 1e-6,
        dangling_redistribution: bool = False,
        passage_self_loops: float = 0.0,
        hub_devaluation: bool = False,
        hub_penalty_mode: str = "none",
        hub_penalty_alpha: float = 1.0,
        hub_penalty_base: float = 2.0,
        symmetric_norm: str = "off",
        community_balance: bool = False,
        community_balance_alpha: float = 0.0,
        community_walk_penalty: bool = False,
        community_walk_alpha: float = 0.5,
        neural_teleportation: Optional[List[float]] = None,
        neural_weight: float = 0.5,
        neural_cosine_threshold: float = 0.0,
        neural_cosine_power: float = 1.0,
        neural_gate_threshold: float = 0.0,
        reranker_scores: Optional[Dict[str, float]] = None,
        reranker_gate_threshold: float = 0.0,
        reranker_teleport_weight: float = 0.0,
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """Run Personalized PageRank with weighted seeds.

        Power iteration on the weighted undirected graph. Both entity and
        passage nodes can be seeds. After convergence, passage node scores
        become document/chunk rankings and entity node scores become
        synthesis evidence.

        Args:
            entity_seeds: {entity_id: weight} — from triple linking.
            passage_seeds: {sentence_id: weight} — from DPR (score * passage_node_weight).
            damping: Damping factor (default 0.5, upstream HippoRAG 2).
            max_iterations: Max power iteration steps.
            convergence_threshold: L1 convergence threshold.
            dangling_redistribution: If True, mass from dangling nodes
                (zero out-degree) teleports back to the personalization
                vector instead of being lost.
            passage_self_loops: If > 0, add virtual self-loops of this
                weight to passage nodes during the walk.
            hub_devaluation: Legacy flag — if True, uses raw-degree IDF.
                Prefer hub_penalty_mode="log" instead.
            hub_penalty_mode: Hub penalty strategy for entity nodes.
                "none" = no penalty (default, backward compat).
                "log"  = 1/log(B+degree)^alpha — tunable hub tax.
            hub_penalty_alpha: Exponent for log hub penalty (default 1.0).
                Higher values (1.5, 2.0) create stronger hub suppression.
            hub_penalty_base: Base for log hub penalty (default 2.0).
                Lower values (1.1) create sharper differentiation.
            symmetric_norm: Symmetric normalization mode.
                "off" = standard row normalization D⁻¹·A (default).
                "all" = D^(-½)·A·D^(-½) on all edges.
                "entity_only" = symmetric norm only for entity↔entity
                    edges, standard norm for MENTIONS (passage↔entity).
            community_balance: If True, weight entity seeds inversely
                by community density.
            community_balance_alpha: Exponent for community balance.
                0.0 (default) = use log formula: seed /= log(2+size).
                >0  = use power-law: seed /= size^alpha.
                E.g. 0.3 gives 1.87x ratio, 0.5 gives 2.83x ratio.
            neural_teleportation: Query embedding vector for Neural PPR.
                When provided, every passage node gets a teleportation
                weight proportional to cosine(query_emb, passage_emb).
                Blended with structural seeds via neural_weight.
            neural_weight: Blend ratio for neural teleportation [0,1].
                0.0 = structural seeds only (original behavior).
                1.0 = pure neural teleportation (cosine-only).
                0.5 = equal blend (recommended starting point).
            neural_gate_threshold: Cosine gate threshold for passage nodes.
                If > 0 and neural_teleportation is provided, passage nodes
                whose cosine(query, passage_emb) < threshold are BLOCKED
                from accumulating PPR mass. Unlike teleportation (additive),
                gating is subtractive — it removes noise passages from the
                walk entirely, redistributing their mass to relevant ones.
                Works independently of neural_weight (can gate with weight=0).
            reranker_scores: Pre-computed cross-encoder scores per passage.
                Dict[sentence_id, relevance_score]. Used for reranker gate
                and/or reranker teleportation. Per APPNP: "predict then
                propagate" — the reranker predicts, PPR propagates.
            reranker_gate_threshold: Minimum reranker score to survive.
                Passages below this are gated (zeroed each iteration).
                Cross-encoder scores are much more discriminative than
                cosine, so this gate is effective where cosine gate fails.
            reranker_teleport_weight: If > 0, blend reranker scores into
                PPR personalization vector (like neural_weight but using
                cross-encoder scores instead of cosine).

        Returns:
            Tuple of:
                - passage_scores: [(sentence_id, score)] sorted desc
                - entity_scores: [(entity_name, score)] sorted desc
        """
        if self._node_count == 0:
            return [], []

        # Build structural personalization vector (entity + passage seeds)
        structural_p = [0.0] * self._node_count

        for node_id, weight in entity_seeds.items():
            idx = self._node_to_idx.get(node_id)
            if idx is not None:
                structural_p[idx] += weight

        for node_id, weight in passage_seeds.items():
            idx = self._node_to_idx.get(node_id)
            if idx is not None:
                structural_p[idx] += weight

        # Neural cosine computation: used for teleportation AND/OR gating
        neural_p = [0.0] * self._node_count
        neural_active = False
        gated_passages: set = set()  # passage indices blocked by neural gate
        need_cosines = (
            (neural_teleportation is not None and self._passage_embeddings)
            and (neural_weight > 0 or neural_gate_threshold > 0)
        )
        if need_cosines:
            import numpy as np
            q = np.array(neural_teleportation, dtype=np.float32)
            q_norm = np.linalg.norm(q)
            if q_norm > 0:
                q = q / q_norm
                passage_indices = []
                passage_embs = []
                for node_id, emb in self._passage_embeddings.items():
                    idx = self._node_to_idx.get(node_id)
                    if idx is not None:
                        passage_indices.append(idx)
                        passage_embs.append(emb)
                if passage_embs:
                    mat = np.array(passage_embs, dtype=np.float32)
                    norms = np.linalg.norm(mat, axis=1, keepdims=True)
                    norms = np.maximum(norms, 1e-10)
                    mat = mat / norms
                    raw_cosines = mat @ q  # shape: (n_passages,)
                    raw_cosines = np.maximum(raw_cosines, 0.0)

                    # Neural gate: block passages below gate threshold
                    if neural_gate_threshold > 0:
                        for i, idx in enumerate(passage_indices):
                            if raw_cosines[i] < neural_gate_threshold:
                                gated_passages.add(idx)
                        logger.info(
                            "neural_gate_applied",
                            total_passages=len(passage_indices),
                            gated=len(gated_passages),
                            surviving=len(passage_indices) - len(gated_passages),
                            gate_threshold=neural_gate_threshold,
                        )

                    # Neural teleportation (only if weight > 0)
                    if neural_weight > 0:
                        cosines = raw_cosines.copy()
                        if neural_cosine_threshold > 0:
                            cosines = np.where(cosines >= neural_cosine_threshold, cosines, 0.0)
                        if neural_cosine_power != 1.0:
                            cosines = cosines ** neural_cosine_power
                        for i, idx in enumerate(passage_indices):
                            neural_p[idx] = float(cosines[i])
                        neural_active = True
                        nonzero_count = int(np.count_nonzero(cosines))
                        logger.info(
                            "neural_teleportation_computed",
                            passages=len(passage_indices),
                            nonzero=nonzero_count,
                            max_cosine=float(np.max(cosines)),
                            min_cosine=float(np.min(cosines)),
                            mean_cosine=float(np.mean(cosines)),
                            neural_weight=neural_weight,
                            cosine_threshold=neural_cosine_threshold,
                            cosine_power=neural_cosine_power,
                        )

        # Reranker gate & teleportation: cross-encoder scores (more discriminative than cosine)
        if reranker_scores:
            # Build reranker gate set
            for node_id, score in reranker_scores.items():
                if reranker_gate_threshold > 0 and score < reranker_gate_threshold:
                    idx = self._node_to_idx.get(node_id)
                    if idx is not None:
                        gated_passages.add(idx)

            # Reranker teleportation: blend reranker scores into personalization
            if reranker_teleport_weight > 0:
                reranker_p = [0.0] * self._node_count
                for node_id, score in reranker_scores.items():
                    idx = self._node_to_idx.get(node_id)
                    if idx is not None and score > 0:
                        reranker_p[idx] = score
                rr_total = sum(reranker_p)
                if rr_total > 0:
                    reranker_p = [p / rr_total for p in reranker_p]
                    # Blend: structural * (1-w) + reranker * w
                    s_total = sum(structural_p)
                    if s_total > 0:
                        structural_p = [p / s_total for p in structural_p]
                    personalization = [
                        (1.0 - reranker_teleport_weight) * structural_p[i]
                        + reranker_teleport_weight * reranker_p[i]
                        for i in range(self._node_count)
                    ]
                    neural_active = False  # skip cosine blending — reranker supersedes

            surviving_count = sum(
                1 for idx in range(self._node_count)
                if self._node_types.get(idx) == "passage" and idx not in gated_passages
            )
            logger.info(
                "reranker_gate_applied",
                total_scored=len(reranker_scores),
                gated=len(gated_passages),
                surviving=surviving_count,
                gate_threshold=reranker_gate_threshold,
                teleport_weight=reranker_teleport_weight,
            )

        # Blend structural and neural personalization
        if neural_active:
            # Normalize each component independently before blending
            s_total = sum(structural_p)
            n_total = sum(neural_p)
            if s_total > 0:
                structural_p = [p / s_total for p in structural_p]
            if n_total > 0:
                neural_p = [p / n_total for p in neural_p]
            personalization = [
                (1.0 - neural_weight) * structural_p[i] + neural_weight * neural_p[i]
                for i in range(self._node_count)
            ]
        else:
            personalization = structural_p

        # Community-balanced personalization: boost sparse communities
        if community_balance and self._community_sizes:
            for idx in range(self._node_count):
                if personalization[idx] > 0 and idx in self._community_id:
                    cid = self._community_id[idx]
                    c_size = self._community_sizes.get(cid, 1)
                    if community_balance_alpha > 0:
                        # Power-law: 1/size^alpha — sharper differentiation
                        personalization[idx] /= c_size ** community_balance_alpha
                    else:
                        # Log formula (legacy default): 1/log(2+size)
                        personalization[idx] /= math.log(2 + c_size)

        # Normalize personalization to sum to 1
        total_p = sum(personalization)
        if total_p <= 0:
            logger.warning("ppr_no_valid_seeds")
            return [], []
        personalization = [p / total_p for p in personalization]

        # Precompute effective out-weight sums with virtual self-loops
        effective_out_sum = dict(self._out_weight_sum)
        if passage_self_loops > 0:
            for idx in range(self._node_count):
                if self._node_types.get(idx) == "passage":
                    effective_out_sum[idx] = effective_out_sum.get(idx, 0.0) + passage_self_loops

        # Precompute hub penalty factors (entity nodes only)
        hub_factor: Dict[int, float] = {}
        effective_hub_mode = hub_penalty_mode
        if hub_devaluation and hub_penalty_mode == "none":
            effective_hub_mode = "raw"  # legacy backward compat
        if effective_hub_mode != "none":
            for idx in range(self._node_count):
                if self._node_types.get(idx) == "entity":
                    degree = max(len(self._adj.get(idx, [])), 1)
                    if effective_hub_mode == "log":
                        hub_factor[idx] = 1.0 / math.log(hub_penalty_base + degree) ** hub_penalty_alpha
                    elif effective_hub_mode == "raw":
                        hub_factor[idx] = 1.0 / degree

        # Precompute sqrt of out-weight sums for symmetric normalization
        sqrt_out: Dict[int, float] = {}
        use_symmetric = symmetric_norm in ("all", "entity_only")
        if use_symmetric:
            for idx in range(self._node_count):
                s = effective_out_sum.get(idx, 0.0)
                sqrt_out[idx] = math.sqrt(s) if s > 0 else 0.0

        # Precompute community walk penalty factors (entity nodes only).
        # factor = 1/(degree × community_size)^α — combines structural
        # hub penalty with community size penalty for maximum differentiation.
        community_factor: Dict[int, float] = {}
        if community_walk_penalty and self._community_sizes:
            for idx in range(self._node_count):
                if self._node_types.get(idx) == "entity" and idx in self._community_id:
                    cid = self._community_id[idx]
                    csize = self._community_sizes.get(cid, 1)
                    degree = max(len(self._adj.get(idx, [])), 1)
                    influence = degree * csize
                    community_factor[idx] = 1.0 / influence ** community_walk_alpha

        # Initialize rank to personalization vector
        rank = list(personalization)

        # Power iteration with weighted edges
        for iteration in range(max_iterations):
            new_rank = [
                (1.0 - damping) * personalization[i]
                for i in range(self._node_count)
            ]

            dangling_mass = 0.0
            for src in range(self._node_count):
                if rank[src] == 0.0:
                    continue
                out_sum = effective_out_sum.get(src, 0.0)
                if out_sum == 0.0:
                    # Dangling node: accumulate mass for redistribution
                    if dangling_redistribution:
                        dangling_mass += damping * rank[src]
                    continue

                # Virtual self-loop: passage retains some mass
                if passage_self_loops > 0 and self._node_types.get(src) == "passage":
                    self_share = damping * rank[src] * passage_self_loops / out_sum
                    new_rank[src] += self_share

                for tgt, edge_weight in self._adj[src]:
                    # Determine if symmetric norm applies to this edge
                    apply_sym = False
                    if use_symmetric:
                        if symmetric_norm == "all":
                            apply_sym = True
                        elif symmetric_norm == "entity_only":
                            # Only entity↔entity edges get symmetric norm
                            apply_sym = (
                                self._node_types.get(src) == "entity"
                                and self._node_types.get(tgt) == "entity"
                            )

                    if apply_sym:
                        # D^(-½)·A·D^(-½): divide by sqrt(deg_src * deg_tgt)
                        sqrt_src = sqrt_out.get(src, 0.0)
                        sqrt_tgt = sqrt_out.get(tgt, 0.0)
                        if sqrt_src > 0 and sqrt_tgt > 0:
                            share = damping * rank[src] * edge_weight / (sqrt_src * sqrt_tgt)
                        else:
                            continue
                    else:
                        # Standard row normalization: D⁻¹·A
                        share = damping * rank[src] * edge_weight / out_sum

                    # Hub penalty: reduce share from high-degree entity nodes
                    if src in hub_factor:
                        share *= hub_factor[src]

                    # Community walk penalty: reduce share from entities in
                    # large communities. Leaked mass tracked for redistribution.
                    if src in community_factor:
                        share *= community_factor[src]

                    new_rank[tgt] += share

            # Redistribute dangling mass to personalization vector
            if dangling_redistribution and dangling_mass > 0:
                for i in range(self._node_count):
                    new_rank[i] += dangling_mass * personalization[i]

            # Community walk penalty: redistribute leaked mass via
            # personalization (forced restart). This is mass-conserving —
            # the total mass removed from large-community entity outflows
            # returns to the system as additional restart mass.
            if community_factor:
                leaked = 0.0
                for src in range(self._node_count):
                    if rank[src] > 0 and src in community_factor:
                        # Mass that would have been sent without penalty
                        full_out = damping * rank[src]
                        # Mass actually sent = full_out * community_factor
                        leaked += full_out * (1.0 - community_factor[src])
                if leaked > 0:
                    for i in range(self._node_count):
                        new_rank[i] += leaked * personalization[i]

            # Neural gate: zero out mass at gated passage nodes.
            # Their mass is effectively lost, causing other passages to
            # receive proportionally more on subsequent iterations via restart.
            if gated_passages:
                for idx in gated_passages:
                    new_rank[idx] = 0.0

            # Check convergence (L1 norm)
            diff = sum(abs(new_rank[i] - rank[i]) for i in range(self._node_count))
            rank = new_rank

            if diff < convergence_threshold:
                logger.debug(
                    "hipporag2_ppr_converged",
                    iteration=iteration,
                    diff=diff,
                )
                break

        # Extract passage scores and entity scores
        passage_scores: List[Tuple[str, float]] = []
        entity_scores: List[Tuple[str, float]] = []

        for idx in range(self._node_count):
            node_id = self._idx_to_node[idx]
            node_type = self._node_types[idx]
            score = rank[idx]

            if node_type == "passage":
                passage_scores.append((node_id, score))
            elif node_type == "entity":
                name = self._node_names[idx]
                entity_scores.append((name, score))

        # Sort descending by score
        passage_scores.sort(key=lambda x: x[1], reverse=True)
        entity_scores.sort(key=lambda x: x[1], reverse=True)

        logger.info(
            "hipporag2_ppr_complete",
            iterations=min(iteration + 1, max_iterations) if self._node_count > 0 else 0,
            entity_seeds=len(entity_seeds),
            passage_seeds=len(passage_seeds),
            hub_penalty=effective_hub_mode,
            hub_penalty_alpha=hub_penalty_alpha,
            hub_penalty_base=hub_penalty_base,
            symmetric_norm=symmetric_norm,
            community_balance=community_balance,
            community_balance_alpha=community_balance_alpha,
            community_count=len(self._community_sizes),
            top_passage_score=passage_scores[0][1] if passage_scores else 0.0,
            top_entity_score=entity_scores[0][1] if entity_scores else 0.0,
        )

        return passage_scores, entity_scores

    def run_appnp(
        self,
        query_embedding: List[float],
        alpha: float = 0.15,
        max_iterations: int = 20,
        convergence_threshold: float = 1e-6,
        entity_seeds: Optional[Dict[str, float]] = None,
        seed_weight: float = 0.0,
        reranker_predictions: Optional[Dict[str, float]] = None,
        self_loop_weight: float = 1.0,
        hub_penalty_mode: str = "none",
        hub_penalty_alpha: float = 1.0,
        hub_penalty_base: float = 2.0,
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """True APPNP: Predict then Propagate (Gasteiger et al., ICLR 2019).

        Follows the paper's exact architecture:
          1. PREDICT: neural predictor scores for ALL passages
          2. PROPAGATE: preds = (1-α)·Â_sym·preds + α·predictions

        The predictor can be:
          - Cosine similarity (default): FREE, uses pre-loaded embeddings.
            Weak discriminator (scores cluster in 0.08-0.18 range).
          - Cross-encoder reranker: one API call (~380ms), highly discriminative.
            This is the APPNP equivalent of a trained MLP predictor.

        Key differences from run_ppr():
          - Personalization = neural predictions for ALL passage nodes
            (not sparse entity seeds)
          - Teleportation → neural predictions (not seed entities)
          - Symmetric normalization D^{-½}·(A+I)·D^{-½} throughout

        Args:
            query_embedding: Query vector for cosine prediction.
            alpha: Teleportation probability back to neural predictions.
                Higher α = more weight on neural predictions (less smoothing).
                Lower α = more graph smoothing (APPNP paper uses 0.1-0.2).
            max_iterations: Max power iteration steps.
            convergence_threshold: L1 convergence threshold.
            entity_seeds: Optional entity seeds to blend into predictions.
                When provided, seed_weight controls the blend ratio.
                This is a hybrid extension: APPNP + structural seeds.
            seed_weight: Blend ratio for entity seeds [0, 1].
                0.0 = pure APPNP (neural predictions only).
                0.5 = equal blend of neural + structural.
                Only used when entity_seeds is provided.
            reranker_predictions: Pre-computed cross-encoder scores
                {sentence_id: relevance_score}. When provided, these
                replace cosine as the prediction signal. This is the
                APPNP equivalent of a trained MLP — highly discriminative.
            hub_penalty_mode: Hub penalty strategy for entity nodes.
                "none" = no penalty (default, backward compat).
                "log"  = 1/log(B+degree)^alpha — tunable hub tax.
                "raw"  = 1/degree — aggressive hub suppression.
            hub_penalty_alpha: Exponent for log hub penalty (default 1.0).
                Higher values (1.5, 2.0) create stronger hub suppression.
            hub_penalty_base: Base for log hub penalty (default 2.0).
                Lower values (1.1) create sharper differentiation.

        Returns:
            Tuple of passage_scores and entity_scores (same as run_ppr).
        """
        import numpy as np

        if self._node_count == 0:
            return [], []

        # ── Step 1: PREDICT ────────────────────────────────────────────
        # Use reranker scores if available (discriminative predictor),
        # otherwise fall back to cosine similarity (weak but free).
        predictions = np.zeros(self._node_count, dtype=np.float64)
        passage_count = 0
        predictor_type = "cosine"

        if reranker_predictions:
            predictor_type = "reranker"
            for node_id, score in reranker_predictions.items():
                idx = self._node_to_idx.get(node_id)
                if idx is not None:
                    predictions[idx] = max(score, 0.0)
                    passage_count += 1
        else:
            # Cosine prediction: FREE, uses pre-loaded embeddings
            q = np.array(query_embedding, dtype=np.float32)
            q_norm = np.linalg.norm(q)
            if q_norm == 0:
                logger.warning("appnp_zero_query_embedding")
                return [], []
            q = q / q_norm

            for node_id, emb in self._passage_embeddings.items():
                idx = self._node_to_idx.get(node_id)
                if idx is None:
                    continue
                e = np.array(emb, dtype=np.float32)
                e_norm = np.linalg.norm(e)
                if e_norm > 0:
                    cos = float(np.dot(q, e / e_norm))
                    predictions[idx] = max(cos, 0.0)  # ReLU: no negative mass
                    passage_count += 1

        # Optionally blend entity seeds into predictions
        if entity_seeds and seed_weight > 0:
            structural = np.zeros(self._node_count, dtype=np.float64)
            for node_id, weight in entity_seeds.items():
                idx = self._node_to_idx.get(node_id)
                if idx is not None:
                    structural[idx] = weight
            s_sum = structural.sum()
            p_sum = predictions.sum()
            if s_sum > 0:
                structural /= s_sum
            if p_sum > 0:
                predictions /= p_sum
            predictions = (1.0 - seed_weight) * predictions + seed_weight * structural

        # Normalize predictions to form a probability distribution
        pred_sum = predictions.sum()
        if pred_sum > 0:
            predictions /= pred_sum
        else:
            logger.warning("appnp_zero_predictions", passage_count=passage_count)
            return [], []

        logger.info(
            "appnp_predict",
            predictor=predictor_type,
            passages=passage_count,
            nonzero=int(np.count_nonzero(predictions)),
            max_pred=float(np.max(predictions)),
            min_nonzero=float(np.min(predictions[predictions > 0])) if np.any(predictions > 0) else 0.0,
            seed_weight=seed_weight,
            has_entity_seeds=bool(entity_seeds),
        )

        # ── Step 2: PROPAGATE ──────────────────────────────────────────
        # APPNP power iteration with SYMMETRIC normalization:
        #   preds = (1-α) · Â_sym · preds + α · predictions
        #
        # Following the paper's calc_A_hat() exactly:
        #   Â = D^{-½} · (A + I) · D^{-½}
        # The "+I" adds self-loops (renormalization trick, Kipf & Welling 2017).
        # Self-loops let nodes retain their own predictions during propagation
        # instead of having them overwritten by neighbors.

        # Precompute degree WITH self-loops: d_i = Σ_j A_ij + 1 (self-loop)
        # Paper: A = adj_matrix + sp.eye(nnodes); D_vec = np.sum(A, axis=1)
        sqrt_degree = np.zeros(self._node_count, dtype=np.float64)
        self_loop_weight = 1.0  # Paper uses identity matrix (weight=1)
        for idx in range(self._node_count):
            d = self._out_weight_sum.get(idx, 0.0) + self_loop_weight
            sqrt_degree[idx] = math.sqrt(d)

        # Precompute hub penalty factors (entity nodes only).
        # Symmetric normalization divides by √degree but doesn't fully
        # prevent hub entities (e.g. "Owner" with 39 mentions) from
        # flooding mass to all their neighbors. The hub penalty adds
        # an additional multiplicative dampening on entity→neighbor flow.
        hub_factor: Dict[int, float] = {}
        if hub_penalty_mode != "none":
            for idx in range(self._node_count):
                if self._node_types.get(idx) == "entity":
                    degree = max(len(self._adj.get(idx, [])), 1)
                    if hub_penalty_mode == "log":
                        hub_factor[idx] = 1.0 / math.log(hub_penalty_base + degree) ** hub_penalty_alpha
                    elif hub_penalty_mode == "raw":
                        hub_factor[idx] = 1.0 / degree
            if hub_factor:
                logger.info(
                    "appnp_hub_penalty",
                    mode=hub_penalty_mode,
                    alpha=hub_penalty_alpha,
                    base=hub_penalty_base,
                    penalised_entities=len(hub_factor),
                )

        preds = predictions.copy()

        for iteration in range(max_iterations):
            # Teleportation component: α · predictions
            new_preds = alpha * predictions

            # Propagation component: (1-α) · Â_sym · preds
            for src in range(self._node_count):
                if preds[src] == 0.0:
                    continue
                sqrt_src = sqrt_degree[src]

                # Self-loop: node retains some of its own value
                # Paper: A+I means node src has an edge to itself with weight 1
                self_share = (1.0 - alpha) * preds[src] * self_loop_weight / (sqrt_src * sqrt_src)
                new_preds[src] += self_share

                for tgt, edge_weight in self._adj.get(src, []):
                    sqrt_tgt = sqrt_degree[tgt]
                    # D^{-½} · (A+I) · D^{-½}
                    share = (1.0 - alpha) * preds[src] * edge_weight / (sqrt_src * sqrt_tgt)

                    # Hub penalty: reduce mass flow from high-degree entity nodes
                    if src in hub_factor:
                        share *= hub_factor[src]

                    new_preds[tgt] += share

            # Check convergence
            diff = float(np.sum(np.abs(new_preds - preds)))
            preds = new_preds

            if diff < convergence_threshold:
                logger.debug("appnp_converged", iteration=iteration, diff=diff)
                break

        # ── Extract results ────────────────────────────────────────────
        passage_scores: List[Tuple[str, float]] = []
        entity_scores: List[Tuple[str, float]] = []

        for idx in range(self._node_count):
            node_id = self._idx_to_node[idx]
            node_type = self._node_types[idx]
            score = float(preds[idx])

            if node_type == "passage":
                passage_scores.append((node_id, score))
            elif node_type == "entity":
                name = self._node_names[idx]
                entity_scores.append((name, score))

        passage_scores.sort(key=lambda x: x[1], reverse=True)
        entity_scores.sort(key=lambda x: x[1], reverse=True)

        logger.info(
            "appnp_complete",
            predictor=predictor_type,
            alpha=alpha,
            iterations=min(iteration + 1, max_iterations) if self._node_count > 0 else 0,
            passages=passage_count,
            seed_weight=seed_weight,
            top_passage_score=passage_scores[0][1] if passage_scores else 0.0,
            top_entity_score=entity_scores[0][1] if entity_scores else 0.0,
        )

        return passage_scores, entity_scores

    def run_gpr(
        self,
        entity_seeds: Dict[str, float],
        passage_seeds: Dict[str, float],
        num_hops: int = 10,
        hop_profile: str = "ppr",
        hop_weights_csv: str = "",
        damping: float = 0.5,
        hub_penalty_mode: str = "none",
        hub_penalty_alpha: float = 1.0,
        hub_penalty_base: float = 2.0,
        symmetric_norm: str = "off",
        community_balance: bool = False,
        community_balance_alpha: float = 0.0,
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """GPR-GNN style per-hop weighted propagation (ICLR 2021).

        Instead of standard PPR's coupled teleportation+walk loop, this
        separates propagation from aggregation:

        1. H^0 = personalization vector (seed scores)
        2. H^k = A_norm @ H^(k-1) for k = 1..K  (pure graph walk, no restart)
        3. final = Σ γ_k * H^k  (weighted combination of all hops)

        This allows independent control of each hop's contribution.
        Key insight from GPR-GNN: for heterophilic graphs (cross-topic
        passages behind hubs), the optimal per-hop weights differ from
        PPR's exponential decay.

        Args:
            entity_seeds: {entity_id: weight} — same as run_ppr.
            passage_seeds: {sentence_id: weight} — same as run_ppr.
            num_hops: Number of propagation hops K (default 10).
            hop_profile: Weight profile for per-hop combination.
                "ppr": (1-α)*α^k — mimics standard PPR decay.
                "uniform": 1/(K+1) — equal weight for all hops.
                "linear_decay": (K+1-k)/sum — linearly decreasing.
                "far_boost": k+1/sum — linearly increasing (far hops).
                "mid_boost": gaussian centered at K//2.
                "custom": use hop_weights_csv.
            hop_weights_csv: Comma-separated weights for "custom" profile.
                E.g. "1.0,0.8,1.2,1.5,1.0" for 5 hops.
            damping: Used only for "ppr" profile to compute α^k decay.
            hub_penalty_mode: Same as run_ppr.
            hub_penalty_alpha: Same as run_ppr.
            hub_penalty_base: Same as run_ppr.
            symmetric_norm: Same as run_ppr.
            community_balance: Same as run_ppr.
            community_balance_alpha: Same as run_ppr.

        Returns:
            Same as run_ppr: (passage_scores, entity_scores) sorted desc.
        """
        if self._node_count == 0:
            return [], []

        # Build personalization vector (same as run_ppr structural seeds)
        personalization = [0.0] * self._node_count

        for node_id, weight in entity_seeds.items():
            idx = self._node_to_idx.get(node_id)
            if idx is not None:
                personalization[idx] += weight

        for node_id, weight in passage_seeds.items():
            idx = self._node_to_idx.get(node_id)
            if idx is not None:
                personalization[idx] += weight

        # Community-balanced personalization (same logic as run_ppr)
        if community_balance and self._community_sizes:
            for idx in range(self._node_count):
                if personalization[idx] > 0 and idx in self._community_id:
                    cid = self._community_id[idx]
                    c_size = self._community_sizes.get(cid, 1)
                    if community_balance_alpha > 0:
                        personalization[idx] /= c_size ** community_balance_alpha
                    else:
                        personalization[idx] /= math.log(2 + c_size)

        # Normalize personalization to sum to 1
        total_p = sum(personalization)
        if total_p <= 0:
            logger.warning("gpr_no_valid_seeds")
            return [], []
        personalization = [p / total_p for p in personalization]

        # Precompute effective out-weight sums
        effective_out_sum = dict(self._out_weight_sum)

        # Precompute hub penalty factors (entity nodes only)
        hub_factor: Dict[int, float] = {}
        if hub_penalty_mode != "none":
            for idx in range(self._node_count):
                if self._node_types.get(idx) == "entity":
                    degree = max(len(self._adj.get(idx, [])), 1)
                    if hub_penalty_mode == "log":
                        hub_factor[idx] = 1.0 / math.log(hub_penalty_base + degree) ** hub_penalty_alpha

        # Precompute sqrt for symmetric normalization
        sqrt_out: Dict[int, float] = {}
        use_symmetric = symmetric_norm in ("all", "entity_only")
        if use_symmetric:
            for idx in range(self._node_count):
                s = effective_out_sum.get(idx, 0.0)
                sqrt_out[idx] = math.sqrt(s) if s > 0 else 0.0

        # ---- Per-hop propagation (no teleportation restart) ----
        # H^0 = personalization, H^k = A_norm @ H^(k-1)
        hop_results: List[List[float]] = [list(personalization)]  # H^0
        current = list(personalization)

        for hop in range(num_hops):
            next_hop = [0.0] * self._node_count
            for src in range(self._node_count):
                if current[src] == 0.0:
                    continue
                out_sum = effective_out_sum.get(src, 0.0)
                if out_sum == 0.0:
                    continue

                for tgt, edge_weight in self._adj[src]:
                    apply_sym = False
                    if use_symmetric:
                        if symmetric_norm == "all":
                            apply_sym = True
                        elif symmetric_norm == "entity_only":
                            apply_sym = (
                                self._node_types.get(src) == "entity"
                                and self._node_types.get(tgt) == "entity"
                            )

                    if apply_sym:
                        sqrt_src = sqrt_out.get(src, 0.0)
                        sqrt_tgt = sqrt_out.get(tgt, 0.0)
                        if sqrt_src > 0 and sqrt_tgt > 0:
                            share = current[src] * edge_weight / (sqrt_src * sqrt_tgt)
                        else:
                            continue
                    else:
                        share = current[src] * edge_weight / out_sum

                    # Hub penalty
                    if src in hub_factor:
                        share *= hub_factor[src]

                    next_hop[tgt] += share

            # Normalize each hop to sum to 1 to prevent mass explosion/collapse
            hop_total = sum(next_hop)
            if hop_total > 0:
                next_hop = [v / hop_total for v in next_hop]

            hop_results.append(next_hop)
            current = next_hop

        # ---- Compute per-hop weights (γ_k) ----
        K = num_hops
        if hop_profile == "custom" and hop_weights_csv:
            raw = [float(w) for w in hop_weights_csv.split(",")]
            # Pad or truncate to K+1
            gamma = (raw + [0.0] * (K + 1))[:K + 1]
        elif hop_profile == "uniform":
            gamma = [1.0 / (K + 1)] * (K + 1)
        elif hop_profile == "linear_decay":
            raw = [float(K + 1 - k) for k in range(K + 1)]
            s = sum(raw)
            gamma = [w / s for w in raw]
        elif hop_profile == "far_boost":
            raw = [float(k + 1) for k in range(K + 1)]
            s = sum(raw)
            gamma = [w / s for w in raw]
        elif hop_profile == "mid_boost":
            center = K / 2.0
            sigma = max(K / 4.0, 1.0)
            raw = [math.exp(-0.5 * ((k - center) / sigma) ** 2) for k in range(K + 1)]
            s = sum(raw)
            gamma = [w / s for w in raw]
        else:
            # "ppr" profile: mimics standard PPR decay
            alpha = damping
            raw = [(1.0 - alpha) * (alpha ** k) for k in range(K + 1)]
            s = sum(raw)
            gamma = [w / s for w in raw]

        # ---- Weighted combination: final = Σ γ_k * H^k ----
        final = [0.0] * self._node_count
        for k in range(K + 1):
            weight_k = gamma[k]
            if weight_k == 0.0:
                continue
            for i in range(self._node_count):
                final[i] += weight_k * hop_results[k][i]

        # Extract passage scores and entity scores
        passage_scores: List[Tuple[str, float]] = []
        entity_scores: List[Tuple[str, float]] = []

        for idx in range(self._node_count):
            node_id = self._idx_to_node[idx]
            node_type = self._node_types[idx]
            score = final[idx]

            if node_type == "passage":
                passage_scores.append((node_id, score))
            elif node_type == "entity":
                name = self._node_names[idx]
                entity_scores.append((name, score))

        passage_scores.sort(key=lambda x: x[1], reverse=True)
        entity_scores.sort(key=lambda x: x[1], reverse=True)

        logger.info(
            "hipporag2_gpr_complete",
            num_hops=num_hops,
            hop_profile=hop_profile,
            gamma_first3=gamma[:3],
            gamma_last3=gamma[-3:] if len(gamma) >= 3 else gamma,
            hub_penalty=hub_penalty_mode,
            hub_penalty_alpha=hub_penalty_alpha,
            symmetric_norm=symmetric_norm,
            top_passage_score=passage_scores[0][1] if passage_scores else 0.0,
            top_entity_score=entity_scores[0][1] if entity_scores else 0.0,
        )

        return passage_scores, entity_scores

