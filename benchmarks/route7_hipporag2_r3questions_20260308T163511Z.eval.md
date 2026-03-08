# LLM Judge Evaluation Report

**Source:** `route7_hipporag2_r3questions_20260308T163511Z.json`
**Judge Model:** `gpt-5.1`
**Date:** 2026-03-08 16:45:11

## Summary Metrics

- **Total Score:** 49/57 (86.0%)
- **Pass Rate (Score >= 2):** 94.7%
- **Evaluated Questions:** 19

## Comparison with Route 6

| Route | Score | Pass Rate |
|-------|-------|-----------|
| Route 6 (LazyGraphRAG) | 46/57 (80.7%) | 78.9% |
| **Route 7 (HippoRAG 2)** | **49/57 (86.0%)** | **94.7%** |

## Detailed Results

### Q-G1 ✅ (Score: 2/3)

**Judge Reasoning:** The answer correctly captures most key termination/cancellation rules: 60 days written notice for property management; 3 business days cancellation with full refund and forfeited deposit thereafter for the purchase contract; holding tank contract remains until owner or pumper terminates; warranty terminates if first purchaser sells/moves out. However, it adds an extra rule about the warranty term ending after one year or sixty days that is not in the expected ground truth, and it omits the explicit statement that the warranty is not transferable. Because of this extra, potentially incorrect detail and the missing non-transferability point, the answer is acceptable but incomplete.

**Expected:** Property management: either party may terminate with `60 days written notice`. Purchase contract: customer may cancel within `3 business days` for full refund; afterward deposit is forfeited. Holding tank contract: remains until owner or pumper terminates. Warranty: not transferable; terminates if first purchaser sells/moves out.

---
### Q-G2 ✅ (Score: 3/3)

**Judge Reasoning:** The question asks which documents reference jurisdictions/governing law, and the ground truth lists: Warranty/arbitration (Idaho), purchase contract (Florida), and property management agreement (Hawaii). The actual answer correctly identifies that the purchase contract is governed by Florida law, the property management agreement by Hawaii law, and the builders limited warranty/arbitration by Idaho law. It also adds related jurisdiction/venue references (courts in Idaho, small claims court, etc.), which are consistent and not contradictory. All key facts from the ground truth are present and accurate, so this is a complete and correct answer.

**Expected:** Warranty/arbitration: disputes governed by `State of Idaho` substantive law. Purchase contract: governed by laws of `State of Florida`. Property management agreement: governed by laws of `State of Hawaii`.

---
### Q-G3 ✅ (Score: 2/3)

**Judge Reasoning:** The answer correctly captures most of the key payment responsibilities: the $29,900 total in three installments, the property management commissions (25%/10%), the $75/month advertising, $50/month admin, 10% repair fee, $35/hour scheduling, Hawaii excise tax on fees, and that the owner pays the pumper charges for the holding tank. However, it adds several items not mentioned in the ground truth (e.g., $250 startup fee, credit card fees, media advertising, housekeeping, arbitration cost splits, legal fees, additional compliance costs) that are not part of the requested summary and may be extraneous or speculative relative to the expected answer. Despite the extra detail, the core facts are present and accurate, so it is acceptable but not perfectly aligned with the expected concise summary.

**Expected:** Invoice: `TOTAL/AMOUNT DUE 29900.00`. Purchase contract: $29,900 in 3 installments. Property management: 25%/10% commissions + $75/month advertising + $50/month admin + 10% repair fee + $35/hour scheduling + Hawaii excise tax on fees. Holding tank: owner pays pumper charges; owner files contract changes within 10 business days.

---
### Q-G4 ✅ (Score: 2/3)

**Judge Reasoning:** The ground truth identifies two specific reporting/record‑keeping obligations: (1) the pumper submitting detailed service reports to the County, and (2) the property management agent providing the owner with a monthly income/expense statement. The actual answer correctly includes both of these, but it also lists many additional obligations that are not purely reporting/record‑keeping (e.g., inspections, rent collection, tax IDs, scheduling service calls). Because it is not limited to the explicitly described reporting/record‑keeping obligations and adds extraneous items, it is acceptable but incomplete/overinclusive rather than fully correct.

**Expected:** Holding tank: pumper submits reports to County including service dates, volumes pumped, and condition. Property management: agent provides owner a monthly statement of income and expenses.

---
### Q-G5 ✅ (Score: 2/3)

**Judge Reasoning:** The answer correctly identifies binding arbitration with a small-claims carveout and describes arbitration administration and procedures, which aligns with the warranty’s dispute-resolution mechanism. However, it omits the confidentiality aspect of the arbitration and does not mention the purchase contract remedy that allows the contractor to recover legal fees upon customer default. It also adds many procedural/arbitration details that were not required by the question. Thus it is mostly correct but incomplete on key points.

**Expected:** Warranty: binding arbitration (with small claims carveout) and confidentiality language. Purchase contract: legal fees recoverable by contractor upon customer default.

---
### Q-G6 ❌ (Score: 1/3)

**Judge Reasoning:** The answer correctly identifies the four key named parties/organizations from the ground truth (Fabrikam Inc., Contoso Ltd., Contoso Lifts LLC, Walt Flood Realty) and associates them with the correct document types. However, it introduces several additional named entities (Contoso, Fabrikam, Bayfront Animal Clinic, Fabrikam Construction, John Smith Company, John Doe) that are not part of the expected ground truth, and it does not clearly map the roles (builder, pumper, customer, owner, agent, etc.) as specified. Because of these extra, likely spurious entities and the omission of role information, the response is only partially correct rather than acceptable or complete.

**Expected:** `Fabrikam Inc.`: builder (warranty), pumper (holding tank), customer (purchase contract) `Contoso Ltd.`: owner (property management), holding tank owner (holding tank) `Contoso Lifts LLC`: contractor (purchase contract) `Walt Flood Realty`: agent (property management)

---
### Q-G7 ✅ (Score: 2/3)

**Judge Reasoning:** The answer correctly captures the key explicit notice/delivery mechanisms: 60 days written notice to terminate the PMA; warranty defect notice must be in writing and sent by certified mail return receipt requested; emergencies may be reported by phone; and filing contract changes with the municipality/County within 10 business days. However, it also includes several additional written-notice requirements (e.g., listing agreement notice, purchase contract changes, filing original contract) that go beyond the explicit mechanisms highlighted in the expected ground truth. While not factually wrong, this extra material makes the answer less focused on the specific summary requested, so it is acceptable but not perfectly aligned with the expected answer.

**Expected:** PMA: `60 days written notice` to terminate Warranty: defect notice must be `in writing` and sent by `certified mail return receipt requested`; emergencies by phone Holding tank: file contract changes with municipality/County within `10 business days`

---
### Q-G8 ✅ (Score: 3/3)

**Judge Reasoning:** The actual answer correctly identifies and accurately summarizes both explicit clauses: (1) the hold harmless/indemnity provision in favor of the agent, with the correct exception for gross negligence or willful misconduct, and (2) the liability insurance requirement with the correct minimum limits ($300,000 BI and $25,000 PD) and the requirement to name the agent as additional insured. This fully matches the expected ground truth with no contradictions or omissions.

**Expected:** PMA: requires liability insurance with minimum limits `$300,000` BI and `$25,000` PD; hold harmless/indemnify agent (except gross negligence/willful misconduct)

---
### Q-G9 ✅ (Score: 3/3)

**Judge Reasoning:** The actual answer correctly identifies both explicit non-refundable/forfeiture terms: the $250 non-refundable start-up fee in the PMA and the forfeiture of the deposit in the purchase contract after the initial period. This matches the expected ground truth with no contradictions or omissions.

**Expected:** PMA: `non-refundable start-up fee` of `$250.00` Purchase contract: after 3 business days, `deposit is forfeited`

---
### Q-G10 ✅ (Score: 2/3)

**Judge Reasoning:** The answer correctly summarizes the main purposes of the Warranty, Holding Tank Servicing Contract, and Property Management Agreement, and mostly captures the purchase contract but omits key elements: it does not mention delivery, payment terms, or cancellation, and it also fails to summarize the invoice document at all. Thus most but not all key facts are present, with some important omissions.

**Expected:** Warranty: limited warranty + arbitration process and exclusions Holding tank: servicing/reporting obligations between owner and pumper PMA: agent manages/rents property, fees, responsibilities, and termination Invoice: amount due for lift purchase Purchase contract: scope of work + payments + delivery + cancellation

---
### Q-N1 ✅ (Score: 3/3)

**Judge Reasoning:** The expected ground truth is that the bank routing number is not specified, and the actual answer correctly states that the requested information was not found in the documents. This matches the requirement for a negative test with no fabrication.

**Expected:** Not specified.

---
### Q-N2 ✅ (Score: 3/3)

**Judge Reasoning:** This is a negative test where the correct response is that the information is not specified. The actual answer correctly states that the requested information was not found in the documents and does not fabricate any IBAN or SWIFT/BIC details.

**Expected:** Not specified.

---
### Q-N3 ✅ (Score: 3/3)

**Judge Reasoning:** This is a negative test where the correct response is that the information is not specified. The actual answer correctly states that the requested information was not found in the available documents and does not fabricate any VAT/Tax ID number. Therefore, it fully matches the expected ground truth.

**Expected:** Not specified.

---
### Q-N5 ✅ (Score: 3/3)

**Judge Reasoning:** This is a negative test where the correct response is to state that the information is not specified. The actual answer correctly indicates that the requested bank account number is not found in the documents and does not fabricate any details.

**Expected:** Not specified.

---
### Q-N6 ✅ (Score: 3/3)

**Judge Reasoning:** This is a negative test: the ground truth indicates that California is not referenced in any documents. The actual answer correctly states that the requested information was not found in the available documents and does not fabricate any details. Therefore, it fully matches the expected behavior.

**Expected:** None (California not referenced).

---
### Q-N7 ✅ (Score: 3/3)

**Judge Reasoning:** This is a negative test where the correct response is to state that the information is not specified. The actual answer correctly indicates that the requested license number was not found in the documents and does not fabricate any details.

**Expected:** Not specified.

---
### Q-N8 ✅ (Score: 3/3)

**Judge Reasoning:** The expected ground truth indicates that the wire transfer / ACH instructions are not specified. The actual answer correctly states that the requested information was not found in the available documents, which aligns with the ground truth for a negative test. No fabrication or contradiction is present.

**Expected:** Not specified.

---
### Q-N9 ✅ (Score: 3/3)

**Judge Reasoning:** This is a negative test where the correct response is to state that the information is not specified. The actual answer correctly indicates that the requested clause about mold damage coverage was not found in the documents and does not fabricate any details.

**Expected:** Not specified.

---
### Q-N10 ✅ (Score: 3/3)

**Judge Reasoning:** The ground truth is that the shipping method / 'SHIPPED VIA' field is not specified or blank. The system answer correctly states that the requested information was not found in the available documents, which aligns with the expected ground truth for this negative test. No fabrication or contradiction is present.

**Expected:** Not specified / blank.  ## G) Synthesis Gap Questions — Frontier Categories (20) These questions target four categories of **synthesis/reasoning limitations** that persist even when retrieval is perfect. They benchmark LLM reasoning quality independently of retrieval architecture. Any route that retrieves complete evidence will face these challenges. See: `ARCHITECTURE_DESIGN_LAZY_HIPPO_HYBRID.md` Section 33.17 for full gap analysis.  ### G.1) Numerical Aggregation (Q-A)

---
