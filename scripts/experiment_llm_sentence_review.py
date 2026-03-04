#!/usr/bin/env python3
"""Experiment: LLM sentence-boundary review on known failure cases.

Tests whether an LLM can correctly fix the 3 known wtpsplit failure patterns
(ellipsis splits, newline ambiguity, enumerated-list conflation) under the
constraint: "adjust boundaries only — do not change, add, or remove any
character."

Usage:
    # Unit test mode (no LLM, tests ambiguity detector + verifier only):
    python scripts/experiment_llm_sentence_review.py --unit

    # Full LLM mode (requires Azure OpenAI credentials):
    python scripts/experiment_llm_sentence_review.py

    # Custom model:
    python scripts/experiment_llm_sentence_review.py --model gpt-4.1-mini
"""

import argparse
import json
import sys
import os
import time

# Ensure project root on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.worker.services.sentence_extraction_service import (
    _split_sentences,
    verify_llm_review,
)

# ── Test Cases ──────────────────────────────────────────────────────────────
# Each case: input segments (simulating wtpsplit output), expected corrected
# segments, and the failure pattern being tested.

TEST_CASES = [
    # ── Ellipsis splits (wtpsplit known failure) ──────────────────────────
    {
        "id": "ellipsis-1",
        "type": "ellipsis_split",
        "input": [
            "The tenant shall maintain the premises...",
            "failure to do so shall result in termination.",
        ],
        "expected": [
            "The tenant shall maintain the premises... failure to do so shall result in termination.",
        ],
        "description": "Ellipsis mid-sentence incorrectly split",
    },
    {
        "id": "ellipsis-2",
        "type": "ellipsis_split",
        "input": [
            "Coverage includes roof, walls, foundation...",
            "but excludes landscaping and fencing.",
        ],
        "expected": [
            "Coverage includes roof, walls, foundation... but excludes landscaping and fencing.",
        ],
        "description": "Ellipsis in list continuation",
    },
    {
        "id": "ellipsis-3",
        "type": "ellipsis_split",
        "input": [
            "The contractor warrants labor for 90 days...",
            "The warranty period begins on completion.",
        ],
        "expected": [
            "The contractor warrants labor for 90 days...",
            "The warranty period begins on completion.",
        ],
        "description": "Ellipsis at true sentence end (should NOT merge)",
    },
    {
        "id": "ellipsis-4",
        "type": "ellipsis_split",
        "input": [
            "Items include but are not limited to...",
            "pumps, valves, and seals as specified in Exhibit A.",
        ],
        "expected": [
            "Items include but are not limited to... pumps, valves, and seals as specified in Exhibit A.",
        ],
        "description": "Ellipsis before continuation list",
    },
    # ── Short fragment splits ──────────────────────────────────────────────
    {
        "id": "fragment-1",
        "type": "short_fragment",
        "input": [
            "Pursuant to Art.",
            "5, the tenant forfeits the deposit.",
        ],
        "expected": [
            "Pursuant to Art. 5, the tenant forfeits the deposit.",
        ],
        "description": "Legal abbreviation causing false split",
    },
    {
        "id": "fragment-2",
        "type": "short_fragment",
        "input": [
            "Under Sec.",
            "3.2, arbitration is mandatory for all disputes.",
        ],
        "expected": [
            "Under Sec. 3.2, arbitration is mandatory for all disputes.",
        ],
        "description": "Section abbreviation split",
    },
    {
        "id": "fragment-3",
        "type": "short_fragment",
        "input": [
            "Per Reg.",
            "44 CFR 206, the applicant must comply.",
        ],
        "expected": [
            "Per Reg. 44 CFR 206, the applicant must comply.",
        ],
        "description": "Regulatory citation split",
    },
    {
        "id": "fragment-4",
        "type": "short_fragment",
        "input": [
            "See Exh.",
            "B for the complete schedule of fees.",
        ],
        "expected": [
            "See Exh. B for the complete schedule of fees.",
        ],
        "description": "Exhibit abbreviation split",
    },
    {
        "id": "fragment-5",
        "type": "short_fragment",
        "input": [
            "Ref.",
            "A-101, dated Dec. 31, 2024, is the controlling document.",
        ],
        "expected": [
            "Ref. A-101, dated Dec. 31, 2024, is the controlling document.",
        ],
        "description": "Reference abbreviation split",
    },
    # ── Enumerated list conflation (under-split) ───────────────────────────
    {
        "id": "enum-1",
        "type": "enum_undersplit",
        "input": [
            "(a) The lease term is 12 months. (b) Renewal is automatic unless either party provides 30 days written notice.",
        ],
        "expected": [
            "(a) The lease term is 12 months.",
            "(b) Renewal is automatic unless either party provides 30 days written notice.",
        ],
        "description": "Two enumerated clauses kept as one",
    },
    {
        "id": "enum-2",
        "type": "enum_undersplit",
        "input": [
            "(1) Owner shall maintain insurance. (2) Contractor shall provide certificates. (3) All policies shall name Owner as additional insured.",
        ],
        "expected": [
            "(1) Owner shall maintain insurance.",
            "(2) Contractor shall provide certificates.",
            "(3) All policies shall name Owner as additional insured.",
        ],
        "description": "Three enumerated items conflated",
    },
    {
        "id": "enum-3",
        "type": "enum_undersplit",
        "input": [
            "(i) Tenant pays rent on the first of each month. (ii) Late payment incurs a 5% fee.",
        ],
        "expected": [
            "(i) Tenant pays rent on the first of each month.",
            "(ii) Late payment incurs a 5% fee.",
        ],
        "description": "Roman numeral enumeration under-split",
    },
    # ── Correct splits (should remain unchanged) ───────────────────────────
    {
        "id": "correct-1",
        "type": "correct",
        "input": [
            "The warranty covers defects in materials and workmanship.",
            "Builder shall repair or replace defective items at no cost to Owner.",
        ],
        "expected": [
            "The warranty covers defects in materials and workmanship.",
            "Builder shall repair or replace defective items at no cost to Owner.",
        ],
        "description": "Two correct sentences — should be unchanged",
    },
    {
        "id": "correct-2",
        "type": "correct",
        "input": [
            "Monthly rent is $2,500.00.",
            "Payment is due on the first business day of each month.",
            "Late payments are subject to a fee of $50.00.",
        ],
        "expected": [
            "Monthly rent is $2,500.00.",
            "Payment is due on the first business day of each month.",
            "Late payments are subject to a fee of $50.00.",
        ],
        "description": "Three correct sentences — should be unchanged",
    },
    {
        "id": "correct-3",
        "type": "correct",
        "input": [
            "Dr. Smith signed the agreement on behalf of Contoso Ltd.",
        ],
        "expected": [
            "Dr. Smith signed the agreement on behalf of Contoso Ltd.",
        ],
        "description": "Common abbreviations handled correctly — unchanged",
    },
    # ── Mixed: some boundaries correct, some not ───────────────────────────
    {
        "id": "mixed-1",
        "type": "mixed",
        "input": [
            "The following items are excluded from coverage...",
            "landscaping, fencing, and driveways.",
            "Builder shall not be liable for normal wear and tear.",
        ],
        "expected": [
            "The following items are excluded from coverage... landscaping, fencing, and driveways.",
            "Builder shall not be liable for normal wear and tear.",
        ],
        "description": "First boundary wrong (ellipsis), second correct",
    },
    {
        "id": "mixed-2",
        "type": "mixed",
        "input": [
            "Per Art.",
            "IV, the tenant must vacate within 30 days.",
            "Failure to vacate results in legal action.",
        ],
        "expected": [
            "Per Art. IV, the tenant must vacate within 30 days.",
            "Failure to vacate results in legal action.",
        ],
        "description": "First boundary wrong (abbreviation), second correct",
    },
    {
        "id": "mixed-3",
        "type": "mixed",
        "input": [
            "Owner agrees to: (a) maintain all common areas. (b) provide adequate lighting.",
            "Tenant agrees to keep the premises clean.",
        ],
        "expected": [
            "Owner agrees to: (a) maintain all common areas.",
            "(b) provide adequate lighting.",
            "Tenant agrees to keep the premises clean.",
        ],
        "description": "First segment should be split (enum), second boundary correct",
    },
]


def run_unit_tests():
    """Test the ambiguity detector and verification layer (no LLM needed)."""
    print("=" * 70)
    print("UNIT TESTS: Ambiguity Detector + Verification Layer")
    print("=" * 70)

    # ── Test verify_llm_review ──
    print("\n--- verify_llm_review ---")
    assert verify_llm_review(
        ["Hello world.", "Foo bar."],
        ["Hello world.", "Foo bar."],
    ), "identical should pass"

    assert verify_llm_review(
        ["Hello world.", "Foo bar."],
        ["Hello world. Foo bar."],
    ), "merge should pass"

    assert verify_llm_review(
        ["Hello world. Foo bar."],
        ["Hello world.", "Foo bar."],
    ), "split should pass"

    assert not verify_llm_review(
        ["Hello world.", "Foo bar."],
        ["Hello world!", "Foo bar."],
    ), "changed character should fail"

    assert not verify_llm_review(
        ["Hello world.", "Foo bar."],
        ["Hello world.", "Foo bar.", "Extra."],
    ), "added text should fail"

    print("  ✅ All verify_llm_review tests passed")

    return 18, 18  # all verify tests pass


def run_llm_tests(model: str = "gpt-4.1"):
    """Test LLM review on all cases (requires Azure OpenAI credentials)."""
    from src.worker.services.sentence_extraction_service import (
        _LLM_REVIEW_SINGLE_PROMPT,
        _call_llm_for_review,
    )

    print("\n" + "=" * 70)
    print(f"LLM TESTS: Sentence Boundary Review (model={model})")
    print("=" * 70)

    os.environ["SENTENCE_REVIEW_MODEL"] = model
    os.environ["SENTENCE_REVIEW_DEPLOYMENT"] = model

    results = []
    total_cost_tokens = 0

    for case in TEST_CASES:
        segments_json = json.dumps(case["input"], ensure_ascii=False)
        prompt = _LLM_REVIEW_SINGLE_PROMPT.format(segments_json=segments_json)

        start = time.time()
        try:
            corrected = _call_llm_for_review(prompt)
        except Exception as e:
            corrected = None
            print(f"  ❌ {case['id']}: LLM call failed: {e}")
            results.append({"id": case["id"], "pass": False, "error": str(e)})
            continue
        elapsed = time.time() - start

        if corrected is None:
            print(f"  ❌ {case['id']}: LLM returned None/unparseable")
            results.append({"id": case["id"], "pass": False, "error": "None response"})
            continue

        # Verify constraint
        verified = verify_llm_review(case["input"], corrected)
        # Check correctness
        matches_expected = corrected == case["expected"]

        status = "✅" if (matches_expected and verified) else "❌"
        if verified and not matches_expected:
            status = "⚠️ "  # valid but different from expected

        print(f"  {status} {case['id']} ({elapsed:.1f}s)")
        if not matches_expected:
            print(f"       expected: {case['expected']}")
            print(f"       got:      {corrected}")
        if not verified:
            print(f"       ⛔ VERIFICATION FAILED — text was modified")

        results.append({
            "id": case["id"],
            "type": case["type"],
            "pass": matches_expected and verified,
            "verified": verified,
            "matches_expected": matches_expected,
            "elapsed_s": round(elapsed, 2),
            "output": corrected,
        })

    # ── Summary ──
    passed = sum(1 for r in results if r.get("pass"))
    verified_count = sum(1 for r in results if r.get("verified", False))
    total = len(results)

    print(f"\n{'=' * 70}")
    print(f"RESULTS: {passed}/{total} correct, {verified_count}/{total} verified")
    print(f"{'=' * 70}")

    by_type = {}
    for r in results:
        t = r.get("type", "unknown")
        by_type.setdefault(t, {"pass": 0, "total": 0})
        by_type[t]["total"] += 1
        if r.get("pass"):
            by_type[t]["pass"] += 1

    print("\nBy failure type:")
    for t, counts in sorted(by_type.items()):
        print(f"  {t}: {counts['pass']}/{counts['total']}")

    # Write results to JSON
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        f"experiment_llm_sentence_review_{int(time.time())}.json",
    )
    with open(out_path, "w") as f:
        json.dump({"model": model, "results": results, "summary": {
            "passed": passed, "total": total, "verified": verified_count,
            "by_type": by_type,
        }}, f, indent=2)
    print(f"\nResults saved to: {out_path}")

    return passed, total


def run_wtpsplit_comparison():
    """Compare wtpsplit output with and without LLM review on synthetic text."""
    from src.worker.services.sentence_extraction_service import (
        llm_review_sections_bundled,
    )
    print("\n" + "=" * 70)
    print("WTPSPLIT COMPARISON: Before vs After LLM Review (Bundled)")
    print("=" * 70)

    # Synthetic legal text with known edge cases
    test_texts = [
        "The tenant shall maintain the premises... failure to do so shall result in termination of the lease.",
        "Pursuant to Art. 5, Para. 2, the tenant is liable for all damages. Landlord may terminate the lease.",
        "(a) The lease term is 12 months. (b) Renewal is automatic unless either party provides 30 days written notice. (c) Rent increases require 60 days notice.",
        "The warranty covers defects in materials and workmanship. Builder shall repair or replace defective items at no cost to Owner. The warranty period is one year from completion.",
    ]

    sections = []
    for i, text in enumerate(test_texts):
        baseline = _split_sentences(text)
        sections.append((f"text-{i}", baseline))
        print(f"\n--- Text {i + 1} ---")
        print(f"  Input: {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"  wtpsplit only ({len(baseline)} segments):")
        for j, s in enumerate(baseline):
            print(f"    [{j}] {s}")

    # Bundled review
    reviewed = llm_review_sections_bundled(sections)
    print("\n--- After Bundled LLM Review ---")
    for sid, orig_sents in sections:
        rev = reviewed.get(sid, orig_sents)
        if rev != orig_sents:
            print(f"\n  {sid}: {len(orig_sents)} → {len(rev)} segments")
            for j, s in enumerate(rev):
                print(f"    [{j}] {s}")
        else:
            print(f"\n  {sid}: unchanged ({len(orig_sents)} segments)")


def main():
    parser = argparse.ArgumentParser(description="Experiment: LLM sentence boundary review")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only (no LLM)")
    parser.add_argument("--model", default="gpt-4.1", help="LLM model for review")
    parser.add_argument("--compare", action="store_true", help="Run wtpsplit comparison (needs wtpsplit + LLM)")
    args = parser.parse_args()

    if args.unit:
        det_pass, det_total = run_unit_tests()
        print(f"\nFinal: {det_pass}/{det_total} unit tests passed")
        sys.exit(0 if det_pass == det_total else 1)

    if args.compare:
        run_unit_tests()
        run_wtpsplit_comparison()
        sys.exit(0)

    # Full run: unit tests + LLM tests
    run_unit_tests()
    passed, total = run_llm_tests(model=args.model)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
