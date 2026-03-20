#!/usr/bin/env python3
"""Fast PPR retrieval evaluator — checks passage coverage without LLM eval.

For each Q-G question, verifies that required key phrases appear in the
retrieved citations. Reports retrieval recall per question and overall.

Usage:
    # Baseline (no PPR mods)
    python3 scripts/test_ppr_retrieval.py --url http://localhost:8888

    # With hub penalty alpha=1.5
    python3 scripts/test_ppr_retrieval.py --url http://localhost:8888 \
        --config-override hub_penalty_mode=log \
        --config-override hub_penalty_alpha=1.5

    # Compare two configs side-by-side
    python3 scripts/test_ppr_retrieval.py --url http://localhost:8888 --compare \
        --config-override hub_penalty_mode=log \
        --config-override hub_penalty_alpha=1.5
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Ground truth: required key phrases per question
# Each entry: (phrase, source_doc_substring)
# A phrase is "found" if it appears (case-insensitive) in ANY citation text
# from the expected document.
# ---------------------------------------------------------------------------
GROUND_TRUTH: Dict[str, Dict[str, Any]] = {
    "Q-G1": {
        "query": "Across the agreements, list the termination/cancellation rules you can find.",
        "required": [
            ("sixty (60) day", "PROPERTY MANAGEMENT"),
            ("3 business days", "purchase_contract"),
            ("deposit is forfeited", "purchase_contract"),
            ("terminat", "HOLDING TANK"),  # "terminates" or "terminate"
            ("not transferable", "WARRANTY"),
        ],
    },
    "Q-G2": {
        "query": "Identify which documents reference jurisdictions / governing law.",
        "required": [
            ("State of Idaho", "WARRANTY"),
            ("Pocatello", "WARRANTY"),
            ("State of Florida", "purchase_contract"),
            ("State of Hawaii", "PROPERTY MANAGEMENT"),
        ],
    },
    "Q-G3": {
        "query": "Summarize who pays what across the set (fees/charges/taxes).",
        "required": [
            ("29,900", "purchase_contract"),
            ("25%", "PROPERTY MANAGEMENT"),
            ("10%", "PROPERTY MANAGEMENT"),
            ("$75", "PROPERTY MANAGEMENT"),
            ("excise tax", "PROPERTY MANAGEMENT"),
            ("pumper", "HOLDING TANK"),
        ],
    },
    "Q-G4": {
        "query": "What obligations are explicitly described as reporting / record-keeping?",
        "required": [
            ("report", "HOLDING TANK"),  # pumper submits reports
            ("volumes in gallons", "HOLDING TANK"),
            ("monthly statement", "PROPERTY MANAGEMENT"),
        ],
    },
    "Q-G5": {
        "query": "What remedies / dispute-resolution mechanisms are described?",
        "required": [
            ("arbitration", "WARRANTY"),
            ("small claims", "WARRANTY"),
            ("confidential", "WARRANTY"),
            ("legal fees", "purchase_contract"),
        ],
    },
    "Q-G6": {
        "query": "List all named parties/organizations across the documents and which document(s) they appear in.",
        "required": [
            ("Fabrikam", "WARRANTY"),
            ("Contoso", "PROPERTY MANAGEMENT"),
            ("Contoso Lifts", "purchase_contract"),
            ("Walt Flood", "PROPERTY MANAGEMENT"),
        ],
    },
    "Q-G7": {
        "query": "Summarize all explicit notice / delivery mechanisms mentioned.",
        "required": [
            ("written noti", "PROPERTY MANAGEMENT"),
            ("certified mail", "WARRANTY"),
            ("business days", "HOLDING TANK"),
        ],
    },
    "Q-G8": {
        "query": "Summarize all explicit insurance / indemnity / hold harmless clauses.",
        "required": [
            ("300,000", "PROPERTY MANAGEMENT"),
            ("25,000", "PROPERTY MANAGEMENT"),
            ("indemnify", "PROPERTY MANAGEMENT"),
            ("negligence", "PROPERTY MANAGEMENT"),
        ],
    },
    "Q-G9": {
        "query": "Identify all explicit non-refundable / forfeiture terms across the documents.",
        "required": [
            ("non-refundable", "PROPERTY MANAGEMENT"),
            ("$250", "PROPERTY MANAGEMENT"),
            ("deposit is forfeited", "purchase_contract"),
        ],
    },
    "Q-G10": {
        "query": "Summarize each document's main purpose in one sentence.",
        "required": [
            ("warranty", "WARRANTY"),
            ("servic", "HOLDING TANK"),
            ("manag", "PROPERTY MANAGEMENT"),
            ("purchase", "purchase_contract"),
        ],
    },
}


def query_api(
    url: str,
    query: str,
    group_id: str,
    force_route: str,
    query_mode: str,
    config_overrides: Dict[str, str],
) -> Dict[str, Any]:
    """Send a query and return the full response."""
    payload = {
        "query": query,
        "group_id": group_id,
        "force_route": force_route,
        "query_mode": query_mode,
        "config_overrides": config_overrides,
        "include_context": True,  # needed for ppr_top_passages
    }
    headers = {
        "Content-Type": "application/json",
        "X-Group-ID": group_id,
    }
    req = urllib.request.Request(
        f"{url}/hybrid/query",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode("utf-8", errors="replace")[:200]}
    except Exception as e:
        return {"error": str(e)}


def check_retrieval(
    ppr_passages: List[Dict[str, Any]],
    required: List[Tuple[str, str]],
) -> List[Dict[str, Any]]:
    """Check which required phrases appear in raw PPR top passages.

    Tests the PPR retrieval layer directly — before reranking and synthesis.
    Each PPR passage has 'sentence_id', 'score', and 'text' (250 chars).
    """
    results = []
    for phrase, doc_substr in required:
        found = False
        found_in = None
        found_rank = -1
        for rank, p in enumerate(ppr_passages):
            text = (p.get("text") or "").lower()
            if phrase.lower() in text:
                found = True
                found_rank = rank
                found_in = f"PPR rank {rank} (score={p.get('score', '?')})"
                break
        results.append({
            "phrase": phrase,
            "expected_doc": doc_substr,
            "found": found,
            "found_in": found_in,
            "ppr_rank": found_rank,
        })
    return results


def run_evaluation(
    url: str,
    group_id: str,
    force_route: str,
    query_mode: str,
    config_overrides: Dict[str, str],
    questions: Optional[List[str]] = None,
    repeats: int = 1,
) -> Dict[str, Any]:
    """Run retrieval evaluation for all Q-G questions."""
    results = {}
    total_found = 0
    total_required = 0

    qids = questions or sorted(GROUND_TRUTH.keys())

    for qid in qids:
        if qid not in GROUND_TRUTH:
            print(f"  [{qid}] ⚠ Not in ground truth, skipping")
            continue

        gt = GROUND_TRUTH[qid]
        query = gt["query"]
        required = gt["required"]

        # Run multiple repeats to check consistency
        repeat_results = []
        for r in range(repeats):
            t0 = time.time()
            resp = query_api(url, query, group_id, force_route, query_mode, config_overrides)
            elapsed = time.time() - t0

            if "error" in resp:
                print(f"  [{qid}] repeat {r+1}: ERROR {resp['error']}")
                repeat_results.append({"found": 0, "total": len(required), "elapsed": elapsed})
                continue

            # Extract raw PPR passages from metadata (pre-reranking)
            metadata = resp.get("metadata", {})
            ppr_passages = metadata.get("ppr_top_passages", [])
            if not ppr_passages:
                print(f"  [{qid}] repeat {r+1}: ⚠ No ppr_top_passages in metadata")

            checks = check_retrieval(ppr_passages, required)
            found = sum(1 for c in checks if c["found"])

            repeat_results.append({
                "found": found,
                "total": len(required),
                "elapsed": elapsed,
                "checks": checks,
                "num_ppr_passages": len(ppr_passages),
            })

        # Aggregate repeats
        best = max(repeat_results, key=lambda x: x["found"])
        worst = min(repeat_results, key=lambda x: x["found"])
        avg_found = sum(r["found"] for r in repeat_results) / len(repeat_results)
        avg_elapsed = sum(r["elapsed"] for r in repeat_results) / len(repeat_results)

        total_found += best["found"]
        total_required += len(required)

        # Status icon
        if best["found"] == len(required):
            icon = "✅"
        elif best["found"] >= len(required) * 0.7:
            icon = "🟡"
        else:
            icon = "❌"

        # Show missing phrases from worst run
        missing = []
        if "checks" in worst:
            missing = [c["phrase"] for c in worst["checks"] if not c["found"]]

        results[qid] = {
            "best": best["found"],
            "worst": worst["found"],
            "avg": avg_found,
            "total": len(required),
            "avg_elapsed_s": avg_elapsed,
            "missing": missing,
        }

        miss_str = f" missing=[{', '.join(missing)}]" if missing else ""
        consistency = f"{worst['found']}-{best['found']}" if worst["found"] != best["found"] else str(best["found"])
        print(f"  {icon} [{qid}] {consistency}/{len(required)}{miss_str}  ({avg_elapsed:.1f}s)")

    overall_pct = (total_found / total_required * 100) if total_required > 0 else 0
    return {
        "per_question": results,
        "total_found": total_found,
        "total_required": total_required,
        "overall_pct": overall_pct,
        "config_overrides": config_overrides,
    }


def main():
    parser = argparse.ArgumentParser(description="Fast PPR retrieval evaluator")
    parser.add_argument("--url", default="http://localhost:8888")
    parser.add_argument("--group-id", default="test-5pdfs-v2-fix2")
    parser.add_argument("--force-route", default="hipporag2_community")
    parser.add_argument("--query-mode", default="community_search")
    parser.add_argument("--config-override", action="append", default=[],
                        help="key=value overrides (repeatable)")
    parser.add_argument("--repeats", type=int, default=1,
                        help="Repeats per question (check PPR consistency)")
    parser.add_argument("--questions", nargs="+", default=None,
                        help="Specific question IDs (e.g. Q-G1 Q-G9)")
    parser.add_argument("--compare", action="store_true",
                        help="Run baseline first, then with overrides")
    parser.add_argument("--json", type=str, default=None,
                        help="Save results to JSON file")
    args = parser.parse_args()

    config_overrides = {}
    for ov in args.config_override:
        k, v = ov.split("=", 1)
        config_overrides[k] = v

    ov_str = " ".join(f"{k}={v}" for k, v in config_overrides.items()) if config_overrides else "(baseline)"
    print(f"\n{'='*70}")
    print(f"PPR Retrieval Evaluator")
    print(f"  URL: {args.url}")
    print(f"  Group: {args.group_id}")
    print(f"  Route: {args.force_route} / {args.query_mode}")
    print(f"  Config: {ov_str}")
    print(f"  Repeats: {args.repeats}")
    print(f"{'='*70}\n")

    if args.compare and config_overrides:
        # Run baseline first
        print("--- BASELINE (no overrides) ---")
        baseline = run_evaluation(
            args.url, args.group_id, args.force_route, args.query_mode,
            {}, args.questions, args.repeats,
        )
        print(f"\n  Baseline: {baseline['total_found']}/{baseline['total_required']} "
              f"({baseline['overall_pct']:.1f}%)\n")

        # Then run with overrides
        print(f"--- EXPERIMENT ({ov_str}) ---")
        experiment = run_evaluation(
            args.url, args.group_id, args.force_route, args.query_mode,
            config_overrides, args.questions, args.repeats,
        )
        print(f"\n  Experiment: {experiment['total_found']}/{experiment['total_required']} "
              f"({experiment['overall_pct']:.1f}%)\n")

        # Comparison
        print("--- COMPARISON ---")
        print(f"  {'QID':<8} {'Baseline':>10} {'Experiment':>12} {'Delta':>8}")
        print(f"  {'-'*40}")
        for qid in sorted(GROUND_TRUTH.keys()):
            if args.questions and qid not in args.questions:
                continue
            b = baseline["per_question"].get(qid, {})
            e = experiment["per_question"].get(qid, {})
            bt = f"{b.get('best',0)}/{b.get('total',0)}"
            et = f"{e.get('best',0)}/{e.get('total',0)}"
            delta = e.get("best", 0) - b.get("best", 0)
            delta_str = f"+{delta}" if delta > 0 else str(delta)
            icon = "📈" if delta > 0 else ("📉" if delta < 0 else "➖")
            print(f"  {icon} {qid:<6} {bt:>10} {et:>12} {delta_str:>8}")
        bd = baseline["total_found"]
        ed = experiment["total_found"]
        delta = ed - bd
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        print(f"  {'-'*40}")
        print(f"  {'TOTAL':<8} {bd}/{baseline['total_required']:>7} "
              f"{ed}/{experiment['total_required']:>9} {delta_str:>8}")

        if args.json:
            with open(args.json, "w") as f:
                json.dump({"baseline": baseline, "experiment": experiment}, f, indent=2)
            print(f"\n  Results saved to {args.json}")
    else:
        result = run_evaluation(
            args.url, args.group_id, args.force_route, args.query_mode,
            config_overrides, args.questions, args.repeats,
        )
        print(f"\n  Overall: {result['total_found']}/{result['total_required']} "
              f"({result['overall_pct']:.1f}%)")

        if args.json:
            with open(args.json, "w") as f:
                json.dump(result, f, indent=2)
            print(f"  Results saved to {args.json}")

    print()


if __name__ == "__main__":
    main()
