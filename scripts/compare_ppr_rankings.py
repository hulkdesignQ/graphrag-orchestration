#!/usr/bin/env python3
"""PPR ranking comparator — shows passage rank/score changes between configs.

Runs each question twice (baseline + experiment), then compares:
- Per-passage rank and score deltas
- Score distribution (top, p50, spread, Gini)
- Biggest promotions/demotions

Usage:
    python3 scripts/compare_ppr_rankings.py --url http://localhost:8888 \
        --config-override hub_penalty_mode=log \
        --config-override hub_penalty_alpha=1.5

    # Single question deep-dive:
    python3 scripts/compare_ppr_rankings.py --url http://localhost:8888 \
        --questions Q-G2 --top 30 \
        --config-override hub_penalty_mode=log \
        --config-override hub_penalty_alpha=1.5
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple


QUESTIONS: Dict[str, str] = {
    "Q-G1": "Across the agreements, list the termination/cancellation rules you can find.",
    "Q-G2": "Identify which documents reference jurisdictions / governing law.",
    "Q-G3": "Summarize who pays what across the set (fees/charges/taxes).",
    "Q-G4": "What obligations are explicitly described as reporting / record-keeping?",
    "Q-G5": "What remedies / dispute-resolution mechanisms are described?",
    "Q-G6": "List all named parties/organizations across the documents and which document(s) they appear in.",
    "Q-G7": "Summarize all explicit notice / delivery mechanisms mentioned.",
    "Q-G8": "Summarize all explicit insurance / indemnity / hold harmless clauses.",
    "Q-G9": "Identify all explicit non-refundable / forfeiture terms across the documents.",
    "Q-G10": "Summarize each document's main purpose in one sentence.",
}


def query_api(
    url: str, query: str, group_id: str, force_route: str,
    query_mode: str, config_overrides: Dict[str, str],
) -> Dict[str, Any]:
    payload = {
        "query": query, "group_id": group_id,
        "force_route": force_route, "query_mode": query_mode,
        "config_overrides": config_overrides, "include_context": True,
    }
    headers = {"Content-Type": "application/json", "X-Group-ID": group_id}
    req = urllib.request.Request(
        f"{url}/hybrid/query",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def gini_coefficient(scores: List[float]) -> float:
    """Gini coefficient: 0=perfect equality, 1=one passage has all mass."""
    if not scores or sum(scores) == 0:
        return 0.0
    sorted_s = sorted(scores)
    n = len(sorted_s)
    total = sum(sorted_s)
    cumsum = 0.0
    gini_sum = 0.0
    for i, s in enumerate(sorted_s):
        cumsum += s
        gini_sum += (2 * (i + 1) - n - 1) * s
    return gini_sum / (n * total)


def compare_question(
    url: str, qid: str, query: str, group_id: str,
    force_route: str, query_mode: str,
    config_overrides: Dict[str, str], top_n: int = 20,
) -> Optional[Dict[str, Any]]:
    """Run baseline and experiment for one question, compare rankings."""
    # Baseline
    t0 = time.time()
    resp_base = query_api(url, query, group_id, force_route, query_mode, {})
    t_base = time.time() - t0
    if "error" in resp_base:
        print(f"  [{qid}] baseline ERROR: {resp_base['error']}")
        return None
    base_passages = resp_base.get("metadata", {}).get("ppr_top_passages", [])

    # Experiment
    t0 = time.time()
    resp_exp = query_api(url, query, group_id, force_route, query_mode, config_overrides)
    t_exp = time.time() - t0
    if "error" in resp_exp:
        print(f"  [{qid}] experiment ERROR: {resp_exp['error']}")
        return None
    exp_passages = resp_exp.get("metadata", {}).get("ppr_top_passages", [])

    if not base_passages or not exp_passages:
        print(f"  [{qid}] ⚠ No PPR passages returned")
        return None

    # Build rank/score maps: sentence_id -> (rank, score, text)
    base_map: Dict[str, Tuple[int, float, str]] = {}
    for i, p in enumerate(base_passages):
        sid = p["sentence_id"]
        base_map[sid] = (i, p["score"], p.get("text", ""))

    exp_map: Dict[str, Tuple[int, float, str]] = {}
    for i, p in enumerate(exp_passages):
        sid = p["sentence_id"]
        exp_map[sid] = (i, p["score"], p.get("text", ""))

    # All sentence IDs present in either
    all_sids = set(base_map.keys()) | set(exp_map.keys())
    max_rank = max(len(base_passages), len(exp_passages))

    # Compute deltas
    comparisons = []
    for sid in all_sids:
        b_rank, b_score, b_text = base_map.get(sid, (max_rank, 0.0, ""))
        e_rank, e_score, e_text = exp_map.get(sid, (max_rank, 0.0, ""))
        text = b_text or e_text
        rank_delta = b_rank - e_rank  # positive = promoted (lower rank = better)
        score_delta = e_score - b_score
        comparisons.append({
            "sid": sid,
            "base_rank": b_rank,
            "exp_rank": e_rank,
            "rank_delta": rank_delta,
            "base_score": b_score,
            "exp_score": e_score,
            "score_delta": score_delta,
            "text": text[:100],
            "in_base": sid in base_map,
            "in_exp": sid in exp_map,
        })

    # Sort by experiment rank (best first)
    comparisons.sort(key=lambda x: x["exp_rank"])

    # Distribution stats
    base_scores = [p["score"] for p in base_passages]
    exp_scores = [p["score"] for p in exp_passages]

    stats = {
        "base_top": base_scores[0] if base_scores else 0,
        "exp_top": exp_scores[0] if exp_scores else 0,
        "base_p50": sorted(base_scores)[len(base_scores)//2] if base_scores else 0,
        "exp_p50": sorted(exp_scores)[len(exp_scores)//2] if exp_scores else 0,
        "base_gini": gini_coefficient(base_scores),
        "exp_gini": gini_coefficient(exp_scores),
        "base_count": len(base_passages),
        "exp_count": len(exp_passages),
        "base_time": t_base,
        "exp_time": t_exp,
    }

    # Biggest movers (>3 rank change)
    promoted = [c for c in comparisons if c["rank_delta"] > 3]
    promoted.sort(key=lambda x: x["rank_delta"], reverse=True)
    demoted = [c for c in comparisons if c["rank_delta"] < -3]
    demoted.sort(key=lambda x: x["rank_delta"])

    # New entries (in experiment but not baseline)
    new_entries = [c for c in comparisons if not c["in_base"] and c["in_exp"]]
    # Dropped entries (in baseline but not experiment)
    dropped = [c for c in comparisons if c["in_base"] and not c["in_exp"]]

    return {
        "qid": qid,
        "comparisons": comparisons,
        "stats": stats,
        "promoted": promoted,
        "demoted": demoted,
        "new_entries": new_entries,
        "dropped": dropped,
        "top_n": top_n,
    }


def print_result(result: Dict[str, Any]) -> None:
    qid = result["qid"]
    stats = result["stats"]
    comparisons = result["comparisons"]
    top_n = result["top_n"]

    print(f"\n{'='*80}")
    print(f"  {qid}: {QUESTIONS.get(qid, '?')}")
    print(f"{'='*80}")

    # Distribution stats
    gini_delta = stats["exp_gini"] - stats["base_gini"]
    gini_arrow = "↓more equal" if gini_delta < -0.01 else ("↑more concentrated" if gini_delta > 0.01 else "≈same")
    top_ratio = stats["exp_top"] / stats["base_top"] if stats["base_top"] > 0 else 0

    print(f"  Score distribution:")
    print(f"    {'':12} {'Baseline':>12} {'Experiment':>12} {'Change':>12}")
    print(f"    {'Top score':12} {stats['base_top']:12.6f} {stats['exp_top']:12.6f} {top_ratio:11.2f}x")
    print(f"    {'Median':12} {stats['base_p50']:12.6f} {stats['exp_p50']:12.6f}")
    print(f"    {'Gini':12} {stats['base_gini']:12.4f} {stats['exp_gini']:12.4f}  {gini_arrow}")
    print(f"    {'Passages':12} {stats['base_count']:>12} {stats['exp_count']:>12}")
    print(f"    {'Time (s)':12} {stats['base_time']:12.1f} {stats['exp_time']:12.1f}")

    # Top N passages comparison
    print(f"\n  Top {top_n} passages (sorted by experiment rank):")
    print(f"    {'Rank':>4} {'B→E':>6} {'BaseScore':>10} {'ExpScore':>10} {'Δ':>5}  Text")
    print(f"    {'-'*74}")
    for c in comparisons[:top_n]:
        b_r = f"{c['base_rank']}" if c['in_base'] else "NEW"
        e_r = f"{c['exp_rank']}"
        delta = c["rank_delta"]
        if delta > 3:
            arrow = f"↑{delta}"
        elif delta < -3:
            arrow = f"↓{abs(delta)}"
        elif not c["in_base"]:
            arrow = "★NEW"
        else:
            arrow = f"{'↑' if delta > 0 else '↓' if delta < 0 else '='}{abs(delta)}" if delta != 0 else "="
        print(f"    {e_r:>4} {b_r:>3}→{e_r:>2} {c['base_score']:10.6f} {c['exp_score']:10.6f} {arrow:>5}  {c['text'][:55]}")

    # Biggest movers
    if result["promoted"]:
        print(f"\n  📈 Biggest promotions (moved up >3 ranks):")
        for c in result["promoted"][:5]:
            print(f"    rank {c['base_rank']}→{c['exp_rank']} (+{c['rank_delta']})  {c['text'][:65]}")

    if result["demoted"]:
        print(f"\n  📉 Biggest demotions (moved down >3 ranks):")
        for c in result["demoted"][:5]:
            print(f"    rank {c['base_rank']}→{c['exp_rank']} ({c['rank_delta']})  {c['text'][:65]}")

    if result["new_entries"]:
        print(f"\n  ★ New entries (not in baseline top-K):")
        for c in result["new_entries"][:5]:
            print(f"    exp rank {c['exp_rank']}  score={c['exp_score']:.6f}  {c['text'][:60]}")

    if result["dropped"]:
        print(f"\n  ✗ Dropped (in baseline but not experiment top-K):")
        for c in result["dropped"][:5]:
            print(f"    was rank {c['base_rank']}  score={c['base_score']:.6f}  {c['text'][:60]}")


def main():
    parser = argparse.ArgumentParser(description="PPR ranking comparator")
    parser.add_argument("--url", default="http://localhost:8888")
    parser.add_argument("--group-id", default="test-5pdfs-v2-fix2")
    parser.add_argument("--force-route", default="hipporag2_community")
    parser.add_argument("--query-mode", default="comprehensive_search")
    parser.add_argument("--config-override", action="append", default=[])
    parser.add_argument("--questions", nargs="+", default=None)
    parser.add_argument("--top", type=int, default=20, help="Show top N passages")
    parser.add_argument("--json", type=str, default=None)
    args = parser.parse_args()

    config_overrides = {}
    for ov in args.config_override:
        k, v = ov.split("=", 1)
        config_overrides[k] = v

    ov_str = " ".join(f"{k}={v}" for k, v in config_overrides.items())
    print(f"\nPPR Ranking Comparator: baseline vs [{ov_str}]")
    print(f"Route: {args.force_route} / {args.query_mode}\n")

    qids = args.questions or sorted(QUESTIONS.keys())
    all_results = []

    for qid in qids:
        if qid not in QUESTIONS:
            print(f"  [{qid}] unknown question, skipping")
            continue

        result = compare_question(
            args.url, qid, QUESTIONS[qid], args.group_id,
            args.force_route, args.query_mode,
            config_overrides, args.top,
        )
        if result:
            all_results.append(result)
            print_result(result)

    # Summary
    if len(all_results) > 1:
        print(f"\n{'='*80}")
        print(f"  SUMMARY across {len(all_results)} questions")
        print(f"{'='*80}")
        total_promoted = sum(len(r["promoted"]) for r in all_results)
        total_demoted = sum(len(r["demoted"]) for r in all_results)
        total_new = sum(len(r["new_entries"]) for r in all_results)
        total_dropped = sum(len(r["dropped"]) for r in all_results)
        avg_gini_base = sum(r["stats"]["base_gini"] for r in all_results) / len(all_results)
        avg_gini_exp = sum(r["stats"]["exp_gini"] for r in all_results) / len(all_results)
        print(f"  Passages promoted >3 ranks: {total_promoted}")
        print(f"  Passages demoted  >3 ranks: {total_demoted}")
        print(f"  New entries:                {total_new}")
        print(f"  Dropped entries:            {total_dropped}")
        print(f"  Avg Gini (baseline):        {avg_gini_base:.4f}")
        print(f"  Avg Gini (experiment):      {avg_gini_exp:.4f}")

    if args.json and all_results:
        # Serialize results
        out = []
        for r in all_results:
            out.append({
                "qid": r["qid"],
                "stats": r["stats"],
                "promoted_count": len(r["promoted"]),
                "demoted_count": len(r["demoted"]),
                "new_count": len(r["new_entries"]),
                "dropped_count": len(r["dropped"]),
                "top_passages": r["comparisons"][:r["top_n"]],
            })
        with open(args.json, "w") as f:
            json.dump({"config": config_overrides, "results": out}, f, indent=2)
        print(f"\n  Results saved to {args.json}")

    print()


if __name__ == "__main__":
    main()
