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
            ("sixty (60) day", "PROPERTY MANAGEMENT"),       # PMA termination notice
            ("written notice", "PROPERTY MANAGEMENT"),       # PMA: written notice to terminate
            ("confirmed reservations", "PROPERTY MANAGEMENT"), # PMA: owner honors confirmed reservations
            ("3 business days", "purchase_contract"),        # purchase: cancellation window
            ("deposit is forfeited", "purchase_contract"),   # purchase: forfeiture after window
            ("pumper terminates", "HOLDING TANK"),             # holding tank: remains until terminated
            ("sells", "WARRANTY"),                           # warranty: terminates if purchaser sells/moves
            ("one (1) year", "WARRANTY"),                    # warranty: terms terminate 1 year
            ("survive", "WARRANTY"),                         # warranty: arbitration provisions survive termination
        ],
    },
    "Q-G2": {
        "query": "Identify which documents reference jurisdictions / governing law.",
        "required": [
            ("State of Idaho", "WARRANTY"),
            ("Pocatello", "WARRANTY"),
            ("State of Florida", "purchase_contract"),
            ("State of Hawaii", "PROPERTY MANAGEMENT"),
            ("SPS 383", "HOLDING TANK"),                     # WI Code SPS 383.21(2)5
            ("Washburn", "HOLDING TANK"),                    # County of Washburn
        ],
    },
    "Q-G3": {
        "query": "Summarize who pays what across the set (fees/charges/taxes).",
        "required": [
            ("29900", "contoso_lifts_invoice"),               # invoice total
            ("29,900", "purchase_contract"),                 # purchase price
            ("20,000", "purchase_contract"),                 # signing installment
            ("25%", "PROPERTY MANAGEMENT"),                  # leasing commission
            ("10%", "PROPERTY MANAGEMENT"),                  # management commission or repair fee
            ("$75", "PROPERTY MANAGEMENT"),                  # advertising fee
            ("$50", "PROPERTY MANAGEMENT"),                  # admin fee
            ("$35", "PROPERTY MANAGEMENT"),                  # scheduling fee
            ("excise tax", "PROPERTY MANAGEMENT"),           # Hawaii excise tax
            ("$250", "PROPERTY MANAGEMENT"),                 # non-refundable start-up fee
            ("credit card", "PROPERTY MANAGEMENT"),          # agent deducts credit card fees
            ("pumper", "HOLDING TANK"),                      # owner pays pumper
            ("no charge", "WARRANTY"),                       # builder repairs at no charge
            ("one-half", "WARRANTY"),                        # each party pays half arbitration
        ],
    },
    "Q-G4": {
        "query": "What obligations are explicitly described as reporting / record-keeping?",
        "required": [
            ("submit to the County, reports", "HOLDING TANK"), # pumper submits reports to county
            ("volumes", "HOLDING TANK"),                     # volumes pumped
            ("sanitary permit", "HOLDING TANK"),             # sanitary permit number
            ("disposal sites", "HOLDING TANK"),               # disposal sites delivered to
            ("Washburn", "HOLDING TANK"),                    # file with County of Washburn
            ("ten (10) business days", "HOLDING TANK"),     # file changes within 10 business days
            ("monthly statement", "PROPERTY MANAGEMENT"),    # agent monthly statement
            ("inspection", "PROPERTY MANAGEMENT"),           # initial property inspection
            ("inventory", "PROPERTY MANAGEMENT"),            # inventory of furniture/furnishings
        ],
    },
    "Q-G5": {
        "query": "What remedies / dispute-resolution mechanisms are described?",
        "required": [
            ("arbitration", "WARRANTY"),                     # binding arbitration
            ("small claims", "WARRANTY"),                    # small claims carveout
            ("confidential", "WARRANTY"),                    # confidentiality language
            ("AAA", "WARRANTY"),                             # administered by AAA
            ("one-half", "WARRANTY"),                        # each party pays half
            ("lien", "WARRANTY"),                            # preserved lien/foreclosure remedies
            ("180 days", "WARRANTY"),                         # 180-day target completion
            ("no charge", "WARRANTY"),                       # builder repairs at no charge within 60 days
            ("legal fees", "purchase_contract"),             # legal fees recoverable
            ("3 business days", "purchase_contract"),          # 3-day cancellation remedy
            ("indemnif", "PROPERTY MANAGEMENT"),             # owner indemnifies agent
        ],
    },
    "Q-G6": {
        "query": "List all named parties/organizations across the documents and which document(s) they appear in.",
        "required": [
            ("Fabrikam", "WARRANTY"),                        # builder in warranty
            ("Fabrikam", "HOLDING TANK"),                    # pumper in holding tank
            ("Contoso", "PROPERTY MANAGEMENT"),              # owner in PMA
            ("Contoso Lifts", "purchase_contract"),          # contractor in purchase
            ("Contoso Lifts", "contoso_lifts_invoice"),      # issuer in invoice
            ("Walt Flood", "PROPERTY MANAGEMENT"),           # agent in PMA
            ("Fabrikam Construction", "contoso_lifts_invoice"), # bill-to customer in invoice
            ("American Arbitration", "WARRANTY"),            # AAA in warranty
            ("Bayfront", "purchase_contract"),               # job name/site
        ],
    },
    "Q-G7": {
        "query": "Summarize all explicit notice / delivery mechanisms mentioned.",
        "required": [
            ("sixty (60) day", "PROPERTY MANAGEMENT"),       # PMA: 60 days written notice to terminate
            ("written notice", "PROPERTY MANAGEMENT"),       # PMA: written notice requirement
            ("five (5) business days", "PROPERTY MANAGEMENT"), # PMA: 5 days notification if listed for sale
            ("Three Hundred", "PROPERTY MANAGEMENT"),        # PMA: prior written approval >$300
            ("certified mail", "WARRANTY"),                  # warranty: certified mail return receipt
            ("telephone the Builder", "WARRANTY"),            # warranty: emergency by phone
            ("in writing", "WARRANTY"),                      # warranty: defect notice in writing
            ("Washburn", "HOLDING TANK"),                    # holding tank: file with County of Washburn
            ("business days", "HOLDING TANK"),               # holding tank: 10 business days filing
            ("submit to the County", "HOLDING TANK"),          # holding tank: pumper submits reports
            ("in writing", "purchase_contract"),             # purchase: changes in writing
            ("may assign this contract", "purchase_contract"), # purchase: assignment requires written consent
        ],
    },
    "Q-G8": {
        "query": "Summarize all explicit insurance / indemnity / hold harmless clauses.",
        "required": [
            ("300,000", "PROPERTY MANAGEMENT"),              # BI limit
            ("25,000", "PROPERTY MANAGEMENT"),               # PD limit
            ("additional insured", "PROPERTY MANAGEMENT"),   # agent named as additional insured
            ("indemnify", "PROPERTY MANAGEMENT"),            # hold harmless/indemnify
            ("negligence", "PROPERTY MANAGEMENT"),           # except gross negligence
            ("holds risk", "purchase_contract"),              # contractor/customer risk allocation
            ("consequential", "WARRANTY"),                   # excludes consequential damages
            ("merchantability", "WARRANTY"),                 # disclaims implied warranties
            ("Failure to promptly notify", "WARRANTY"),      # failure to notify relieves builder
        ],
    },
    "Q-G9": {
        "query": "Identify all explicit non-refundable / forfeiture terms across the documents.",
        "required": [
            ("non-refundable", "PROPERTY MANAGEMENT"),       # PMA start-up fee
            ("$250", "PROPERTY MANAGEMENT"),                 # $250 amount
            ("deposit is forfeited", "purchase_contract"),   # purchase: deposit forfeiture
            ("3 business days", "purchase_contract"),        # after 3 business days
        ],
    },
    "Q-G10": {
        "query": "Summarize each document's main purpose in one sentence.",
        "required": [
            ("Limited Warranty", "WARRANTY"),                  # warranty doc
            ("holding tank", "HOLDING TANK"),                  # holding tank servicing
            ("manag", "PROPERTY MANAGEMENT"),                # property management
            ("Contoso Lifts LLC", "contoso_lifts_invoice"),      # invoice doc
            ("Contoso Lifts", "purchase_contract"),            # purchase contract
        ],
    },
}

# ---------------------------------------------------------------------------
# Q-D (Drift / multi-hop reasoning) retrieval ground truth
# Same format: (substring_in_passage_text, source_document_substring)
# ---------------------------------------------------------------------------
GROUND_TRUTH_QD: Dict[str, Dict[str, Any]] = {
    "Q-D1": {
        "query": "If an emergency defect occurs under the warranty (e.g., burst pipe), what is the required notification channel and consequence of delay?",
        "required": [
            ("telephone", "WARRANTY"),                        # must telephone builder
            ("emergency", "WARRANTY"),                        # emergency defect
            ("promptly notify", "WARRANTY"),                  # failure to promptly notify
            ("relieves", "WARRANTY"),                         # relieves builder of liability
        ],
    },
    "Q-D2": {
        "query": "In the property management agreement, what happens to confirmed reservations if the agreement is terminated or the property is sold?",
        "required": [
            ("confirmed reservations", "PROPERTY MANAGEMENT"),  # honor confirmed reservations
            ("terminat", "PROPERTY MANAGEMENT"),                # if terminated
        ],
    },
    "Q-D3": {
        "query": "Compare 'time windows' across the set: list all explicit day-based timeframes.",
        "required": [
            ("sixty (60) day", "PROPERTY MANAGEMENT"),         # 60 days written notice
            ("3 business days", "purchase_contract"),           # cancellation window
            ("ten (10)", "HOLDING TANK"),                    # 10 business days to file changes
            ("60 days", "WARRANTY"),                           # warranty repair timeline / period
        ],
    },
    "Q-D4": {
        "query": "Which documents mention insurance and what limits are specified?",
        "required": [
            ("300,000", "PROPERTY MANAGEMENT"),                # BI limit
            ("25,000", "PROPERTY MANAGEMENT"),                 # PD limit
            ("additional insured", "PROPERTY MANAGEMENT"),     # agent named additional insured
        ],
    },
    "Q-D5": {
        "query": "In the warranty, explain how the 'coverage start' is defined and what must happen before coverage ends.",
        "required": [
            ("final settlement", "WARRANTY"),                  # coverage start trigger
            ("first occup", "WARRANTY"),                       # or first occupies the home
            ("in writing", "WARRANTY"),                        # claims must be in writing
        ],
    },
    "Q-D6": {
        "query": "Do the purchase contract total price and the invoice total match? If so, what is that amount?",
        "required": [
            ("29,900", "purchase_contract"),                   # purchase contract total
            ("29,900", "contoso_lifts_invoice"),               # invoice total
        ],
    },
    "Q-D7": {
        "query": "Which document has the latest explicit date, and what is it?",
        "required": [
            ("04/30/2025", "purchase_contract"),               # latest date
        ],
    },
    "Q-D8": {
        "query": "Across the set, which entity appears in the most different documents: Fabrikam Inc. or Contoso Ltd.?",
        "required": [
            ("Fabrikam", "WARRANTY"),                           # Fabrikam in warranty
            ("Fabrikam", "HOLDING TANK"),                       # Fabrikam in holding tank
            ("Contoso", "PROPERTY MANAGEMENT"),                 # Contoso in PMA
            ("Contoso", "HOLDING TANK"),                        # Contoso in holding tank
        ],
    },
    "Q-D9": {
        "query": "Compare the 'fees' concepts: which doc has a percentage-based fee structure and which has fixed installment payments?",
        "required": [
            ("25%", "PROPERTY MANAGEMENT"),                    # PMA leasing commission
            ("10%", "PROPERTY MANAGEMENT"),                    # PMA management commission
            ("20,000", "purchase_contract"),                   # 1st installment (signing)
            ("7,000", "purchase_contract"),                    # 2nd installment (delivery)
            ("2,900", "purchase_contract"),                    # 3rd installment (completion)
        ],
    },
    "Q-D10": {
        "query": "List the three different 'risk allocation' statements across the set (risk of loss, liability limitations, non-transferability).",
        "required": [
            ("risk", "purchase_contract"),                     # risk of loss after delivery
            ("negligence", "PROPERTY MANAGEMENT"),             # except gross negligence
            ("not transferable", "WARRANTY"),                  # warranty non-transferable
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
    ground_truth: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Run retrieval evaluation for ground truth questions."""
    gt_dict = ground_truth or GROUND_TRUTH
    results = {}
    total_found = 0
    total_final_found = 0
    total_required = 0

    qids = questions or sorted(gt_dict.keys())

    for qid in qids:
        if qid not in gt_dict:
            print(f"  [{qid}] ⚠ Not in ground truth, skipping")
            continue

        gt = gt_dict[qid]
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

            # Also check post-reranking passages (final_passages)
            final_passages = metadata.get("final_passages", [])
            final_checks = check_retrieval(final_passages, required) if final_passages else []
            final_found = sum(1 for c in final_checks if c["found"])

            repeat_results.append({
                "found": found,
                "total": len(required),
                "elapsed": elapsed,
                "checks": checks,
                "num_ppr_passages": len(ppr_passages),
                "final_found": final_found,
                "num_final_passages": len(final_passages),
                "final_checks": final_checks,
            })

        # Aggregate repeats
        best = max(repeat_results, key=lambda x: x["found"])
        worst = min(repeat_results, key=lambda x: x["found"])
        avg_found = sum(r["found"] for r in repeat_results) / len(repeat_results)
        avg_elapsed = sum(r["elapsed"] for r in repeat_results) / len(repeat_results)

        total_found += best["found"]
        total_required += len(required)

        # Post-reranking recall
        best_final = max(repeat_results, key=lambda x: x.get("final_found", 0))
        worst_final = min(repeat_results, key=lambda x: x.get("final_found", 0))
        total_final_found += best_final.get("final_found", 0)

        # Status icon
        if best["found"] == len(required):
            icon = "✅"
        elif best["found"] >= len(required) * 0.7:
            icon = "🟡"
        else:
            icon = "❌"

        # Post-reranking icon
        ff = best_final.get("final_found", 0)
        if ff == len(required):
            final_icon = "✅"
        elif ff >= len(required) * 0.7:
            final_icon = "🟡"
        else:
            final_icon = "❌"

        # Show missing phrases from worst run
        missing = []
        if "checks" in worst:
            missing = [c["phrase"] for c in worst["checks"] if not c["found"]]

        final_missing = []
        if "final_checks" in worst_final and worst_final["final_checks"]:
            final_missing = [c["phrase"] for c in worst_final["final_checks"] if not c["found"]]

        results[qid] = {
            "best": best["found"],
            "worst": worst["found"],
            "avg": avg_found,
            "total": len(required),
            "avg_elapsed_s": avg_elapsed,
            "missing": missing,
            "final_best": best_final.get("final_found", 0),
            "final_worst": worst_final.get("final_found", 0),
            "final_missing": final_missing,
        }

        miss_str = f" missing=[{', '.join(missing)}]" if missing else ""
        ppr_p = best.get("num_ppr_passages", "?")
        final_p = best_final.get("num_final_passages", "?")
        consistency = f"{worst['found']}-{best['found']}" if worst["found"] != best["found"] else str(best["found"])
        final_str = f"{best_final.get('final_found', 0)}/{len(required)}"
        final_miss_str = f" dropped=[{', '.join(final_missing)}]" if final_missing else ""
        print(f"  {icon} [{qid}] PPR={consistency}/{len(required)} ({ppr_p}p) | {final_icon} Reranked={final_str} ({final_p}p){final_miss_str}{miss_str}  ({avg_elapsed:.1f}s)")

    overall_pct = (total_found / total_required * 100) if total_required > 0 else 0
    final_pct = (total_final_found / total_required * 100) if total_required > 0 else 0
    return {
        "per_question": results,
        "total_found": total_found,
        "total_final_found": total_final_found,
        "total_required": total_required,
        "overall_pct": overall_pct,
        "final_pct": final_pct,
        "config_overrides": config_overrides,
    }


def main():
    parser = argparse.ArgumentParser(description="Fast PPR retrieval evaluator")
    parser.add_argument("--url", default="http://localhost:8888")
    parser.add_argument("--group-id", default="test-5pdfs-v2-fix2")
    parser.add_argument("--force-route", default="hipporag2_community")
    parser.add_argument("--query-mode", default="comprehensive_search")
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
    parser.add_argument("--question-set", default="Q-G",
                        choices=["Q-G", "Q-D", "all"],
                        help="Which question set to evaluate (Q-G=global, Q-D=drift, all=both)")
    args = parser.parse_args()

    config_overrides = {}
    for ov in args.config_override:
        k, v = ov.split("=", 1)
        config_overrides[k] = v

    ov_str = " ".join(f"{k}={v}" for k, v in config_overrides.items()) if config_overrides else "(baseline)"

    # Select ground truth based on question set
    if args.question_set == "Q-D":
        gt_dict = GROUND_TRUTH_QD
        gt_label = "Q-D (drift/multi-hop)"
    elif args.question_set == "all":
        gt_dict = {**GROUND_TRUTH, **GROUND_TRUTH_QD}
        gt_label = "Q-G + Q-D (all)"
    else:
        gt_dict = GROUND_TRUTH
        gt_label = "Q-G (global)"

    total_phrases = sum(len(v["required"]) for v in gt_dict.values())
    print(f"\n{'='*70}")
    print(f"PPR Retrieval Evaluator")
    print(f"  URL: {args.url}")
    print(f"  Group: {args.group_id}")
    print(f"  Route: {args.force_route} / {args.query_mode}")
    print(f"  Config: {ov_str}")
    print(f"  Repeats: {args.repeats}")
    print(f"  Question set: {gt_label} ({total_phrases} phrases)")
    print(f"{'='*70}\n")

    if args.compare and config_overrides:
        # Run baseline first
        print("--- BASELINE (no overrides) ---")
        baseline = run_evaluation(
            args.url, args.group_id, args.force_route, args.query_mode,
            {}, args.questions, args.repeats, ground_truth=gt_dict,
        )
        print(f"\n  Baseline: {baseline['total_found']}/{baseline['total_required']} "
              f"({baseline['overall_pct']:.1f}%)\n")

        # Then run with overrides
        print(f"--- EXPERIMENT ({ov_str}) ---")
        experiment = run_evaluation(
            args.url, args.group_id, args.force_route, args.query_mode,
            config_overrides, args.questions, args.repeats, ground_truth=gt_dict,
        )
        print(f"\n  Experiment: {experiment['total_found']}/{experiment['total_required']} "
              f"({experiment['overall_pct']:.1f}%)\n")

        # Comparison
        print("--- COMPARISON ---")
        print(f"  {'QID':<8} {'Baseline':>10} {'Experiment':>12} {'Delta':>8}")
        print(f"  {'-'*40}")
        for qid in sorted(gt_dict.keys()):
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
            config_overrides, args.questions, args.repeats, ground_truth=gt_dict,
        )
        print(f"\n  PPR recall:      {result['total_found']}/{result['total_required']} "
              f"({result['overall_pct']:.1f}%)")
        print(f"  Reranked recall: {result['total_final_found']}/{result['total_required']} "
              f"({result['final_pct']:.1f}%)")

        if args.json:
            with open(args.json, "w") as f:
                json.dump(result, f, indent=2)
            print(f"  Results saved to {args.json}")

    print()


if __name__ == "__main__":
    main()
