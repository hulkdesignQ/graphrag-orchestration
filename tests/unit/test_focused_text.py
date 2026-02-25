"""
Local test for _focused_text denoising logic.

Compares the OLD substring-matching approach (broken — matches 100% of
sentences with 30 generic entity names) vs the NEW MENTIONS-based approach
(precise graph edges, only top-10 entities).

Also tests the end-to-end denoising effect: simulates multiple chunks
flowing through the pipeline, measuring total context reduction, token
savings, and content fidelity.

Run: python -m pytest tests/unit/test_focused_text.py -v
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any, Dict, List

import pytest


# ── Extracted logic from route_7_hipporag2.py ──


def focused_text_OLD(sentence_texts, full_text, entity_names_lower):
    """OLD approach: Python substring matching with 30 entity names."""
    if not sentence_texts or not entity_names_lower:
        return full_text

    hit_indices = set()
    for i, sent in enumerate(sentence_texts):
        sent_l = sent.lower()
        for en in entity_names_lower:
            if en in sent_l:
                hit_indices.add(i)
                break

    if not hit_indices:
        return full_text

    ranges = []
    for idx in sorted(hit_indices):
        lo = max(0, idx - 1)
        hi = min(len(sentence_texts), idx + 2)
        if ranges and lo <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], hi)
        else:
            ranges.append((lo, hi))

    windows = []
    for lo, hi in ranges:
        windows.append(" ".join(sentence_texts[lo:hi]))
    return " [...] ".join(windows)


def focused_text_NEW(sentence_texts, full_text, hit_indices):
    """NEW approach: pre-computed hit indices from graph MENTIONS edges."""
    if not sentence_texts or not hit_indices:
        return full_text

    ranges = []
    for idx in sorted(hit_indices):
        if idx < 0 or idx >= len(sentence_texts):
            continue
        lo = max(0, idx - 1)
        hi = min(len(sentence_texts), idx + 2)
        if ranges and lo <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], hi)
        else:
            ranges.append((lo, hi))

    if not ranges:
        return full_text

    windows = []
    for lo, hi in ranges:
        windows.append(" ".join(sentence_texts[lo:hi]))
    return " [...] ".join(windows)


# ── Realistic test data ──

# 15 sentences from a typical legal warranty chunk
WARRANTY_SENTENCES = [
    "This Limited Warranty is provided by Builder to Original Owner.",
    "The warranty period begins on the date of closing and extends for one year.",
    "Builder warrants that the home will be free from defects in materials and workmanship.",
    "This warranty does not cover damage caused by acts of nature, including floods and earthquakes.",
    "Owner must provide written notice of any defect within thirty days of discovery.",
    "Builder shall have the right to inspect the property before performing any repairs.",
    "Any dispute arising under this warranty shall be resolved through binding arbitration.",
    "The arbitration shall be conducted under the rules of the American Arbitration Association.",
    "The parties agree that all arbitration proceedings shall be confidential.",
    "Either party may seek provisional remedies in any court of competent jurisdiction.",
    "Claims of three thousand dollars or less may be filed in small claims court.",
    "The arbitration shall take place in Pocatello, Idaho.",
    "Owner must initiate arbitration within one hundred eighty days of the dispute arising.",
    "Each party shall bear its own costs of arbitration unless otherwise ordered.",
    "This warranty is governed by the laws of the State of Idaho.",
]

# 30 entity names from PPR (positions 11-30 are generic noise)
ENTITIES_30 = [
    "builder", "original owner", "american arbitration association",
    "pocatello", "idaho", "limited warranty",
    # Generic noise starting here:
    "party", "state", "act", "contract", "home", "court",
    "owner", "warranty", "property", "date", "notice",
    "damage", "dispute", "claim", "rule", "right",
    "period", "year", "day", "repair", "cost",
    "law", "order", "time",
]

# Top-10 entity names (precise PPR entities)
ENTITIES_10 = [
    "builder", "original owner", "american arbitration association",
    "pocatello", "idaho", "limited warranty",
    "party", "state", "act", "contract",
]

# Graph MENTIONS edges: only sentences that DIRECTLY mention specific entities
# (created during indexing with entity extraction, not substring matching)
# In reality, sentence 0 mentions "Builder" and "Original Owner" explicitly;
# sentence 7 mentions "American Arbitration Association"; etc.
MENTIONS_HIT_INDICES = {0, 7, 11, 14}  # sentences 0, 7, 11, 14


class TestFocusedTextComparison:
    """Compare OLD substring vs NEW MENTIONS-based denoising."""

    def test_old_approach_matches_all_sentences(self):
        """OLD approach: with 30 entity names, nearly ALL sentences match."""
        result = focused_text_OLD(WARRANTY_SENTENCES, "fallback", ENTITIES_30)
        # Count how many sentences were included
        # Since substring matching is so broad, we expect nearly all
        hit_count = 0
        for i, sent in enumerate(WARRANTY_SENTENCES):
            sent_l = sent.lower()
            for en in ENTITIES_30:
                if en in sent_l:
                    hit_count += 1
                    break
        assert hit_count >= 14, f"Expected nearly all sentences to match, got {hit_count}/15"
        # The result should be almost the full text
        full = " ".join(WARRANTY_SENTENCES)
        assert len(result) >= len(full) * 0.95, (
            f"OLD approach should return ~100% of text, "
            f"got {len(result)}/{len(full)} ({len(result)/len(full)*100:.0f}%)"
        )

    def test_old_approach_substring_false_positives(self):
        """Demonstrate specific substring false positives."""
        # "act" matches "contract" (sent 0 has no "act" but has "contract" via other sents)
        # "state" matches "State" in sentence 14
        # "party" matches "parties" or "party" in sentences 8, 9
        # "home" matches "home" in sentence 2
        # "right" matches "right" in sentence 5
        # "day" matches "days" in sentence 4, 12
        # "court" matches "court" in sentence 9, 10
        false_positives = {
            "act": ["contract"],      # "act" in "contract"
            "state": ["State"],       # legit but noisy
            "party": ["party"],       # legit but too broad
            "date": ["date"],         # "date" appears in unrelated context
            "court": ["court"],       # broad match
        }
        for entity, expected_matches in false_positives.items():
            matched_sents = [
                i for i, s in enumerate(WARRANTY_SENTENCES)
                if entity in s.lower()
            ]
            assert len(matched_sents) > 0, f"Expected '{entity}' to match some sentence"

    def test_new_approach_precise_windows(self):
        """NEW approach: only MENTIONS-linked sentences, produces compact text."""
        result = focused_text_NEW(WARRANTY_SENTENCES, "fallback", MENTIONS_HIT_INDICES)
        full = " ".join(WARRANTY_SENTENCES)
        # Should be significantly smaller than full text
        ratio = len(result) / len(full)
        assert ratio < 0.70, (
            f"NEW approach should return <70% of text, "
            f"got {ratio*100:.0f}%"
        )
        # Should contain "[...]" markers between windows
        assert "[...]" in result, "Expected [...] window separators"

    def test_new_approach_no_hits_returns_full_text(self):
        """When no entity MENTIONS hits, fall back to full text."""
        result = focused_text_NEW(WARRANTY_SENTENCES, "full fallback text", set())
        assert result == "full fallback text"

    def test_new_approach_preserves_relevant_content(self):
        """Verify key entity-mentioning sentences are included."""
        result = focused_text_NEW(WARRANTY_SENTENCES, "fallback", MENTIONS_HIT_INDICES)
        # Sentence 0 (Builder, Original Owner)
        assert "Builder" in result
        assert "Original Owner" in result
        # Sentence 7 (American Arbitration Association)
        assert "American Arbitration Association" in result
        # Sentence 11 (Pocatello)
        assert "Pocatello" in result
        # Sentence 14 (Idaho)
        assert "Idaho" in result

    def test_reduction_ratio(self):
        """Quantify the denoising improvement: OLD vs NEW."""
        old_result = focused_text_OLD(WARRANTY_SENTENCES, "fallback", ENTITIES_30)
        new_result = focused_text_NEW(WARRANTY_SENTENCES, "fallback", MENTIONS_HIT_INDICES)
        full = " ".join(WARRANTY_SENTENCES)

        old_ratio = len(old_result) / len(full)
        new_ratio = len(new_result) / len(full)

        print(f"\n--- Denoising comparison ---")
        print(f"Full text:   {len(full)} chars (100%)")
        print(f"OLD (substr): {len(old_result)} chars ({old_ratio*100:.0f}%)")
        print(f"NEW (graph):  {len(new_result)} chars ({new_ratio*100:.0f}%)")
        print(f"Reduction:    {(1 - new_ratio/old_ratio)*100:.0f}% less context")

        # NEW should be at least 30% smaller than OLD
        assert new_ratio < old_ratio * 0.70, (
            f"NEW ({new_ratio*100:.0f}%) should be >=30% smaller than OLD ({old_ratio*100:.0f}%)"
        )

    def test_top10_still_over_matches(self):
        """Even with top-10 entities, substring matching still over-matches."""
        result = focused_text_OLD(WARRANTY_SENTENCES, "fallback", ENTITIES_10)
        full = " ".join(WARRANTY_SENTENCES)
        hit_count = 0
        for sent in WARRANTY_SENTENCES:
            sent_l = sent.lower()
            for en in ENTITIES_10:
                if en in sent_l:
                    hit_count += 1
                    break
        # Even top-10 includes "act" (matches "contract"), "state", "party"
        # which still match the majority of sentences via substring
        assert hit_count >= 9, (
            f"Even top-10 entities match {hit_count}/15 sentences via substring"
        )


class TestMergeHitIndexOffset:
    """Test that entity hit indices are properly offset during chunk merging."""

    def test_offset_after_merge(self):
        """When merging chunk A (10 sents) + chunk B (8 sents),
        chunk B's hit indices should be offset by len(A_sents)."""
        chunk_a_sents = [f"Sentence A{i}." for i in range(10)]
        chunk_b_sents = [f"Sentence B{i}." for i in range(8)]

        # Entity hits: chunk A has hits at {2, 5}, chunk B at {1, 6}
        hits_a = {2, 5}
        hits_b = {1, 6}

        # Simulate merge
        merged_sents = chunk_a_sents + chunk_b_sents
        offset = len(chunk_a_sents)
        merged_hits = hits_a | {idx + offset for idx in hits_b}

        # Expected: {2, 5, 11, 16}
        assert merged_hits == {2, 5, 11, 16}

        # Verify focused_text produces correct windows
        result = focused_text_NEW(merged_sents, "fallback", merged_hits)
        assert "Sentence A2" in result  # hit at index 2
        assert "Sentence A5" in result  # hit at index 5
        assert "Sentence B1" in result  # hit at index 11 (B1)
        assert "Sentence B6" in result  # hit at index 16 (B6)
        assert "[...]" in result  # should have separators between windows

    def test_offset_boundary_merge(self):
        """Hits at boundary of merged chunks should merge windows correctly."""
        chunk_a_sents = [f"A{i}." for i in range(5)]
        chunk_b_sents = [f"B{i}." for i in range(5)]

        # A hit at last sentence of A and first sentence of B
        hits_a = {4}
        hits_b = {0}
        merged_sents = chunk_a_sents + chunk_b_sents
        merged_hits = hits_a | {idx + 5 for idx in hits_b}
        # hits = {4, 5} — adjacent, windows should merge

        result = focused_text_NEW(merged_sents, "fallback", merged_hits)
        # Window for idx=4: lo=3, hi=6 → A3, A4, B0
        # Window for idx=5: lo=4, hi=7 → A4, B0, B1
        # These overlap → merged: lo=3, hi=7 → A3, A4, B0, B1
        assert "A3" in result
        assert "A4" in result
        assert "B0" in result
        assert "B1" in result
        # No [...] separator between these since they merged
        assert "[...]" not in result


class TestEdgeCases:
    """Edge cases for focused_text_NEW."""

    def test_empty_sentences(self):
        result = focused_text_NEW([], "fallback text", {0, 1})
        assert result == "fallback text"

    def test_out_of_range_indices(self):
        sents = ["One.", "Two.", "Three."]
        result = focused_text_NEW(sents, "fallback", {5, 10, -1})
        assert result == "fallback"  # all indices out of range → no ranges → fallback

    def test_single_sentence_chunk(self):
        sents = ["Only sentence."]
        result = focused_text_NEW(sents, "fallback", {0})
        assert result == "Only sentence."

    def test_all_sentences_hit(self):
        sents = ["A.", "B.", "C."]
        result = focused_text_NEW(sents, "fallback", {0, 1, 2})
        # All hit → one merged window covering everything
        assert result == "A. B. C."
        assert "[...]" not in result


# =====================================================================
# Helpers that mirror the Route 7 pipeline (chunk merge + focused text)
# =====================================================================

def _estimate_tokens(text: str) -> int:
    """Same heuristic used by synthesis.py: ~4 chars per token."""
    return len(text) // 4 + 1


def _simulate_pipeline(
    chunks: List[Dict[str, Any]],
    entity_names_30: list[str],
    mentions_hit_map: Dict[str, set],
) -> Dict[str, Any]:
    """Simulate the full Route 7 denoising pipeline on a list of chunks.

    Returns stats for both OLD (substring) and NEW (MENTIONS) approaches.
    """
    old_total_chars = 0
    new_total_chars = 0
    old_texts: list[str] = []
    new_texts: list[str] = []

    ent_lower = {n.lower() for n in entity_names_30}

    for chunk in chunks:
        cid = chunk["chunk_id"]
        sents = chunk["sentence_texts"]
        full = " ".join(sents)

        # OLD: substring matching
        old_result = focused_text_OLD(sents, full, ent_lower)
        old_total_chars += len(old_result)
        old_texts.append(old_result)

        # NEW: graph MENTIONS
        hits = mentions_hit_map.get(cid, set())
        new_result = focused_text_NEW(sents, full, hits)
        new_total_chars += len(new_result)
        new_texts.append(new_result)

    full_chars = sum(len(" ".join(c["sentence_texts"])) for c in chunks)
    return {
        "num_chunks": len(chunks),
        "full_chars": full_chars,
        "full_tokens": _estimate_tokens("x" * full_chars),
        "old_chars": old_total_chars,
        "old_tokens": _estimate_tokens("x" * old_total_chars),
        "new_chars": new_total_chars,
        "new_tokens": _estimate_tokens("x" * new_total_chars),
        "old_texts": old_texts,
        "new_texts": new_texts,
        "old_ratio": old_total_chars / full_chars if full_chars else 0,
        "new_ratio": new_total_chars / full_chars if full_chars else 0,
    }


def _simulate_merge_then_focus(
    chunks: List[Dict[str, Any]],
    mentions_hit_map: Dict[str, set],
) -> List[Dict[str, Any]]:
    """Simulate section-based chunk merging + focused text (NEW only).

    Mirrors the merge logic at route_7_hipporag2.py:1173-1248.
    """
    _MAX_MERGE = 2

    # Group by (document_id, section_title)
    section_groups: dict[tuple, list] = defaultdict(list)
    for c in chunks:
        key = (c.get("document_id", ""), c.get("section_title", ""))
        section_groups[key].append(c)

    merged_results: list[dict] = []
    for _key, group in section_groups.items():
        group.sort(key=lambda x: x.get("chunk_index", 0))
        merged = [dict(group[0])]  # shallow copy
        for r in group[1:]:
            prev = merged[-1]
            prev_idx = prev.get("chunk_index", 0)
            curr_idx = r.get("chunk_index", 0)
            merge_count = len(prev.get("_merged_ids", [prev.get("chunk_id", "")]))
            if curr_idx == prev_idx + 1 and merge_count < _MAX_MERGE:
                prev_sents = prev.get("sentence_texts") or []
                curr_sents = r.get("sentence_texts") or []
                prev_hits = prev.get("_entity_hit_indices") or set()
                curr_hits = r.get("_entity_hit_indices") or set()
                offset = len(prev_sents)
                prev["sentence_texts"] = prev_sents + curr_sents
                prev["_entity_hit_indices"] = prev_hits | {
                    idx + offset for idx in curr_hits
                }
                prev["text"] = (
                    (prev.get("text", "") + " " + r.get("text", "")).strip()
                )
                prev["chunk_index"] = curr_idx
                prev.setdefault("_merged_ids", [prev.get("chunk_id", "")])
                prev["_merged_ids"].append(r.get("chunk_id", ""))
            else:
                merged.append(dict(r))
        merged_results.extend(merged)

    output: list[dict] = []
    for r in merged_results:
        sents = r.get("sentence_texts") or []
        full = r.get("text", "") or " ".join(sents)
        hits = r.get("_entity_hit_indices") or set()
        focused = focused_text_NEW(sents, full, hits)
        output.append({
            "chunk_id": r.get("chunk_id", ""),
            "full_text": full,
            "focused_text": focused,
            "full_chars": len(full),
            "focused_chars": len(focused),
            "sentence_count": len(sents),
            "hit_count": len(hits),
        })
    return output


# =====================================================================
# Realistic multi-document corpus for denoising-effect testing
# =====================================================================

# ── Chunk 1: Legal warranty (15 sentences, sparse entity hits) ──
CHUNK_WARRANTY = {
    "chunk_id": "chunk-warranty-001",
    "document_id": "doc-warranty",
    "section_title": "Limited Warranty",
    "chunk_index": 0,
    "sentence_texts": WARRANTY_SENTENCES,
    "text": " ".join(WARRANTY_SENTENCES),
}

# ── Chunk 2: Financial summary (12 sentences, medium hits) ──
FINANCIAL_SENTENCES = [
    "Total revenue for Q4 2025 was $4.2 million, exceeding the forecast.",
    "Operating expenses increased by 12% compared to Q3.",
    "The gross margin improved to 58%, up from 52% in the prior quarter.",
    "Net income reached $1.1 million after adjusting for one-time charges.",
    "Accounts receivable decreased by $200,000 due to improved collections.",
    "The company repaid $500,000 of its revolving credit facility.",
    "Cash and cash equivalents stood at $3.8 million at quarter end.",
    "Capital expenditures totaled $320,000, primarily for new equipment.",
    "The board approved a quarterly dividend of $0.15 per share.",
    "Earnings per share came in at $0.42, beating analyst estimates.",
    "The company reaffirmed its full-year revenue guidance of $16 million.",
    "Management highlighted strong demand in the enterprise segment.",
]

CHUNK_FINANCIAL = {
    "chunk_id": "chunk-financial-001",
    "document_id": "doc-financial",
    "section_title": "Financial Summary",
    "chunk_index": 0,
    "sentence_texts": FINANCIAL_SENTENCES,
    "text": " ".join(FINANCIAL_SENTENCES),
}

# ── Chunk 3: Technical specification (10 sentences, dense entity hits) ──
TECHNICAL_SENTENCES = [
    "The HyperDrive X200 supports transfer speeds up to 40 Gbps over USB4.",
    "It is backward-compatible with USB 3.2 Gen 2 and Thunderbolt 3.",
    "The unit includes an embedded NVMe SSD controller for direct drive access.",
    "Power delivery is rated at 100W, sufficient for most laptop charging.",
    "The device operates within a temperature range of 0°C to 45°C.",
    "Dual DisplayPort 1.4 outputs support 8K resolution at 60Hz.",
    "An integrated Realtek RTL8156 provides 2.5GbE wired networking.",
    "Firmware updates are delivered via the HyperDrive Companion App.",
    "The enclosure is CNC-machined aluminum with IP54 dust/water rating.",
    "Weight is 180g with dimensions of 120 × 55 × 15 mm.",
]

CHUNK_TECHNICAL = {
    "chunk_id": "chunk-tech-001",
    "document_id": "doc-tech",
    "section_title": "Specifications",
    "chunk_index": 0,
    "sentence_texts": TECHNICAL_SENTENCES,
    "text": " ".join(TECHNICAL_SENTENCES),
}

# ── Chunk 4: Adjacent chunk for merge testing ──
TECHNICAL_SENTENCES_2 = [
    "The HyperDrive X200 ships with a braided USB-C cable of 0.5m length.",
    "Optional accessories include a 1m cable and a carrying pouch.",
    "Warranty coverage extends to two years from the date of purchase.",
    "Support is available at support.hyperdrive.com or via the companion app.",
    "The device has been certified by the USB Implementers Forum.",
    "FCC Part 15 Class B compliance has been verified.",
    "An optional enterprise management license enables fleet deployment.",
    "The companion app is available for Windows 10+, macOS 12+, and Linux.",
]

CHUNK_TECHNICAL_2 = {
    "chunk_id": "chunk-tech-002",
    "document_id": "doc-tech",
    "section_title": "Specifications",
    "chunk_index": 1,
    "sentence_texts": TECHNICAL_SENTENCES_2,
    "text": " ".join(TECHNICAL_SENTENCES_2),
}

# ── 30 PPR entity names (broad, many generic) ──
PPR_ENTITIES_30 = [
    "hyperdrive x200", "q4 2025", "american arbitration association",
    "pocatello", "idaho", "builder", "original owner",
    "realtek rtl8156", "nvme ssd", "usb implementers forum",
    # Generic noise (positions 11-30):
    "company", "board", "party", "state", "date", "revenue",
    "cost", "share", "rate", "unit", "power", "support",
    "range", "device", "app", "drive", "act", "weight",
    "cable", "fund",
]

# ── MENTIONS hit indices (what the graph actually knows) ──
# Sparse: only sentences where an entity was extracted during indexing.
MENTIONS_MAP = {
    "chunk-warranty-001": {0, 7, 11, 14},        # Builder, AAA, Pocatello, Idaho
    "chunk-financial-001": {0, 8, 9},             # Q4 2025, board/dividend, EPS
    "chunk-tech-001": {0, 1, 2, 6},               # HyperDrive X200, USB4, NVMe, RTL8156
    "chunk-tech-002": {0, 4},                      # HyperDrive X200, USB-IF
}


# =====================================================================
# Test class: End-to-end denoising effect
# =====================================================================

class TestDenoisingEffect:
    """Validate that the MENTIONS-based approach materially reduces context
    sent to synthesis, across multiple realistic document types."""

    ALL_CHUNKS = [CHUNK_WARRANTY, CHUNK_FINANCIAL, CHUNK_TECHNICAL, CHUNK_TECHNICAL_2]

    def test_overall_context_reduction(self):
        """Across all chunks, NEW should use ≤70% of full text chars."""
        stats = _simulate_pipeline(self.ALL_CHUNKS, PPR_ENTITIES_30, MENTIONS_MAP)
        assert stats["new_ratio"] <= 0.70, (
            f"NEW context ratio {stats['new_ratio']:.0%} exceeds 70% of full text"
        )

    def test_old_approach_is_nearly_full_text(self):
        """OLD substring approach should return ≥85% of full text."""
        stats = _simulate_pipeline(self.ALL_CHUNKS, PPR_ENTITIES_30, MENTIONS_MAP)
        assert stats["old_ratio"] >= 0.85, (
            f"OLD context ratio {stats['old_ratio']:.0%} is less than 85% — "
            "unexpected, substring matching with 30 entities should be very broad"
        )

    def test_new_is_strictly_smaller_than_old(self):
        """NEW approach must produce strictly less text than OLD."""
        stats = _simulate_pipeline(self.ALL_CHUNKS, PPR_ENTITIES_30, MENTIONS_MAP)
        assert stats["new_chars"] < stats["old_chars"], (
            f"NEW ({stats['new_chars']}) should be < OLD ({stats['old_chars']})"
        )

    def test_token_savings_are_meaningful(self):
        """Token savings should be at least 200 tokens across 4 chunks.
        (With only 4 small test chunks the absolute saving is modest;
        the 20-chunk test below validates savings at realistic scale.)"""
        stats = _simulate_pipeline(self.ALL_CHUNKS, PPR_ENTITIES_30, MENTIONS_MAP)
        saved = stats["old_tokens"] - stats["new_tokens"]
        assert saved >= 200, (
            f"Token savings {saved} is below 200 — denoising effect too weak"
        )

    def test_per_chunk_denoising_varies_by_hit_density(self):
        """Chunks with fewer MENTIONS hits should have a larger reduction."""
        stats = _simulate_pipeline(self.ALL_CHUNKS, PPR_ENTITIES_30, MENTIONS_MAP)

        # warranty: 4 hits in 15 sents → aggressive reduction
        warranty_new = stats["new_texts"][0]
        warranty_full = " ".join(CHUNK_WARRANTY["sentence_texts"])
        warranty_ratio = len(warranty_new) / len(warranty_full)

        # tech: 4 hits in 10 sents → moderate reduction
        tech_new = stats["new_texts"][2]
        tech_full = " ".join(CHUNK_TECHNICAL["sentence_texts"])
        tech_ratio = len(tech_new) / len(tech_full)

        # Sparse chunk (warranty 4/15) should be reduced more than
        # denser chunk (tech 4/10)
        assert warranty_ratio < tech_ratio, (
            f"Sparse warranty ({warranty_ratio:.0%}) should be more reduced "
            f"than denser tech ({tech_ratio:.0%})"
        )

    def test_separator_markers_present_in_sparse_chunks(self):
        """Sparse-hit chunks should have [...] separators between windows."""
        hits = MENTIONS_MAP["chunk-warranty-001"]  # {0, 7, 11, 14}
        result = focused_text_NEW(WARRANTY_SENTENCES, "fallback", hits)
        count = result.count("[...]")
        # 4 non-adjacent hits → should produce multiple windows
        assert count >= 2, (
            f"Expected ≥2 [...] separators for 4 scattered hits, got {count}"
        )

    def test_no_separator_when_hits_are_adjacent(self):
        """Adjacent hits merge into a single window with no separator."""
        sents = [f"S{i}." for i in range(10)]
        result = focused_text_NEW(sents, "fallback", {3, 4, 5})
        # Hits 3,4,5 → windows (2,6) merge → one block, no [...]
        assert "[...]" not in result

    def test_denoised_text_retains_all_entity_sentences(self):
        """Every sentence directly linked by MENTIONS must appear."""
        for chunk in self.ALL_CHUNKS:
            cid = chunk["chunk_id"]
            sents = chunk["sentence_texts"]
            hits = MENTIONS_MAP.get(cid, set())
            if not hits:
                continue
            result = focused_text_NEW(sents, "fallback", hits)
            for idx in hits:
                # The hit sentence itself must be in the output
                assert sents[idx] in result, (
                    f"Chunk {cid}: sentence {idx} ({sents[idx][:40]}...) "
                    "missing from focused output"
                )


class TestDenoisingWithMerge:
    """Test denoising through the chunk-merge pipeline (adjacent same-section
    chunks are merged before focused-text is applied)."""

    def test_merge_reduces_chunk_count(self):
        """Adjacent tech chunks (index 0,1) should merge into one."""
        chunks = [
            {**CHUNK_TECHNICAL, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-001"]},
            {**CHUNK_TECHNICAL_2, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-002"]},
        ]
        output = _simulate_merge_then_focus(chunks, MENTIONS_MAP)
        assert len(output) == 1, f"Expected 1 merged chunk, got {len(output)}"

    def test_merged_chunk_preserves_hits_from_both(self):
        """After merge, hit sentences from both chunks must appear."""
        chunks = [
            {**CHUNK_TECHNICAL, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-001"]},
            {**CHUNK_TECHNICAL_2, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-002"]},
        ]
        output = _simulate_merge_then_focus(chunks, MENTIONS_MAP)
        merged = output[0]
        text = merged["focused_text"]

        # From chunk-tech-001 hit 0: HyperDrive X200 / USB4
        assert "HyperDrive X200" in text
        # From chunk-tech-001 hit 6: RTL8156
        assert "RTL8156" in text or "Realtek" in text
        # From chunk-tech-002 hit 4: USB Implementers Forum
        assert "USB Implementers Forum" in text

    def test_merged_chunk_is_denoised(self):
        """Merged 18-sentence chunk should still be denoised, not full text."""
        chunks = [
            {**CHUNK_TECHNICAL, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-001"]},
            {**CHUNK_TECHNICAL_2, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-002"]},
        ]
        output = _simulate_merge_then_focus(chunks, MENTIONS_MAP)
        merged = output[0]
        ratio = merged["focused_chars"] / merged["full_chars"]
        assert ratio < 0.85, (
            f"Merged chunk ratio {ratio:.0%} ≥ 85% — denoising not effective after merge"
        )

    def test_non_adjacent_chunks_not_merged(self):
        """Chunks from different sections should stay separate."""
        chunks = [
            {**CHUNK_WARRANTY, "_entity_hit_indices": MENTIONS_MAP["chunk-warranty-001"]},
            {**CHUNK_FINANCIAL, "_entity_hit_indices": MENTIONS_MAP["chunk-financial-001"]},
            {**CHUNK_TECHNICAL, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-001"]},
        ]
        output = _simulate_merge_then_focus(chunks, MENTIONS_MAP)
        assert len(output) == 3, f"Expected 3 separate chunks, got {len(output)}"

    def test_merge_respects_max_merge_limit(self):
        """At most 2 chunks merged even if 3 are adjacent."""
        chunk_3 = {
            "chunk_id": "chunk-tech-003",
            "document_id": "doc-tech",
            "section_title": "Specifications",
            "chunk_index": 2,
            "sentence_texts": ["Extra sentence 1.", "Extra sentence 2."],
            "text": "Extra sentence 1. Extra sentence 2.",
            "_entity_hit_indices": {0},
        }
        chunks = [
            {**CHUNK_TECHNICAL, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-001"]},
            {**CHUNK_TECHNICAL_2, "_entity_hit_indices": MENTIONS_MAP["chunk-tech-002"]},
            chunk_3,
        ]
        output = _simulate_merge_then_focus(chunks, MENTIONS_MAP)
        # First two merge → 1 chunk; third stays separate → 2 total
        assert len(output) == 2, f"Expected 2 chunks (2 merged + 1 separate), got {len(output)}"


class TestDenoisingTokenBudgetImpact:
    """Validate that denoising meaningfully reduces token consumption,
    which translates directly to synthesis quality (less noise within budget)
    and cost savings."""

    def test_20_chunk_simulation(self):
        """Simulate a realistic 20-chunk retrieval and measure token impact."""
        # Build 20 chunks of varying sizes (8-16 sentences)
        chunks = []
        hit_map: Dict[str, set] = {}
        for i in range(20):
            n_sents = 8 + (i % 9)  # 8–16 sentences
            sents = [
                f"Document {i} sentence {j} contains important information "
                f"about the contract terms and party obligations."
                for j in range(n_sents)
            ]
            cid = f"chunk-sim-{i:03d}"
            chunks.append({
                "chunk_id": cid,
                "document_id": f"doc-{i // 5}",
                "section_title": f"Section {i % 5}",
                "chunk_index": i % 5,
                "sentence_texts": sents,
                "text": " ".join(sents),
            })
            # Sparse hits: 2 per chunk on average
            hit_map[cid] = {0, n_sents // 2}

        stats = _simulate_pipeline(chunks, PPR_ENTITIES_30, hit_map)

        # With 30 generic entities, OLD should match nearly everything
        assert stats["old_ratio"] >= 0.90, (
            f"OLD approach matched only {stats['old_ratio']:.0%} (expected ≥90%)"
        )
        # NEW should cut context by at least half
        assert stats["new_ratio"] <= 0.55, (
            f"NEW approach ratio {stats['new_ratio']:.0%} exceeds 55%"
        )
        # Absolute token savings
        saved_tokens = stats["old_tokens"] - stats["new_tokens"]
        assert saved_tokens >= 1000, (
            f"Expected ≥1000 token savings across 20 chunks, got {saved_tokens}"
        )

    def test_zero_hit_chunks_use_full_text(self):
        """Chunks with no MENTIONS hits should fall back to full text."""
        chunks = [CHUNK_FINANCIAL]
        empty_map: Dict[str, set] = {}  # no hits for any chunk
        stats = _simulate_pipeline(chunks, PPR_ENTITIES_30, empty_map)
        # NEW falls back to full text when no hits
        assert stats["new_ratio"] == pytest.approx(1.0, abs=0.01), (
            f"Expected ~100% for no-hit chunks, got {stats['new_ratio']:.0%}"
        )

    def test_signal_to_noise_improvement(self):
        """The proportion of entity-relevant sentences in the output should be
        higher with NEW than OLD (better signal-to-noise ratio)."""
        chunk = CHUNK_WARRANTY
        sents = chunk["sentence_texts"]
        hits = MENTIONS_MAP[chunk["chunk_id"]]  # {0, 7, 11, 14}

        # OLD: count how many output sentences are entity-relevant
        old_result = focused_text_OLD(sents, "fallback", PPR_ENTITIES_30)
        old_relevant = sum(1 for idx in hits if sents[idx] in old_result)
        old_total = sum(1 for s in sents if s in old_result)
        old_snr = old_relevant / old_total if old_total else 0

        # NEW: same metric
        new_result = focused_text_NEW(sents, "fallback", hits)
        new_relevant = sum(1 for idx in hits if sents[idx] in new_result)
        new_total_sents = 0
        for s in sents:
            if s in new_result:
                new_total_sents += 1
        new_snr = new_relevant / new_total_sents if new_total_sents else 0

        assert new_snr > old_snr, (
            f"NEW signal-to-noise ({new_snr:.2f}) should exceed "
            f"OLD ({old_snr:.2f})"
        )
