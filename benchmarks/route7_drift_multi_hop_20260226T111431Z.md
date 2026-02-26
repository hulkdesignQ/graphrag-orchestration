# Route 7 (HippoRAG2) Repeatability Benchmark

**Timestamp:** 20260226T111431Z

**API Base URL:** `https://graphrag-api.salmonhill-df6033f3.swedencentral.azurecontainerapps.io`

**Group ID:** `test-5pdfs-v2-fix2`

**Force Route:** `hipporag2_search`

---

## Scenario: hybrid_hipporag2_search_summary

**Response Type:** `summary`

### Q-D1: If an emergency defect occurs under the warranty (e.g., burst pipe), what is the required notification channel and consequence of delay?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.00 |
| Containment | 0.94 |
| Precision | 0.23 |
| Recall | 0.94 |
| F1 Score | 0.37 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 5947 |
| Latency P95 (ms) | 5947 |
| Latency Min (ms) | 5947 |
| Latency Max (ms) | 5947 |

**Run 1 (5947ms):**

```
## Summary

If an emergency defect occurs under the warranty, such as a burst pipe, the Buyer/Owner is required to immediately notify the Builder by telephone using the emergency number provided. Only emergency reports are accepted by phone. Failure to promptly notify the Builder of an emergency relieves the Builder of all liability for replacement, repair, and all other damages related to the defect [1][2].

## Key Points

- The Buyer/Owner must immediately telephone the Builder in the event of...
```

### Q-D2: In the property management agreement, what happens to confirmed reservations if the agreement is terminated or the property is sold?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.09 |
| Containment | 0.83 |
| Precision | 0.10 |
| Recall | 0.83 |
| F1 Score | 0.18 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 3953 |
| Latency P95 (ms) | 3953 |
| Latency Min (ms) | 3953 |
| Latency Max (ms) | 3953 |

**Run 1 (3953ms):**

```
## Summary

If the property management agreement is terminated or the property is sold, the Owner is required to honor all confirmed reservations. Additionally, termination of the agreement does not invalidate any existing rental agreements made by the Agent on the Owner's behalf. The Owner remains responsible for completing all obligations or expenses incurred under the agreement by the Agent, even after termination [1][2].

## Key Points

- Upon termination of the agreement or sale of the prop...
```

### Q-D3: Compare "time windows" across the set: list all explicit day-based timeframes.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.05 |
| Containment | 0.36 |
| Precision | 0.23 |
| Recall | 0.36 |
| F1 Score | 0.28 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 7073 |
| Latency P95 (ms) | 7073 |
| Latency Min (ms) | 7073 |
| Latency Max (ms) | 7073 |

**Run 1 (7073ms):**

```
## Summary

Across the provided documents, explicit day-based timeframes ("time windows") are as follows: The Builder warrants certain items (doors, windows, electric switches, receptacles, fixtures, caulking, plumbing fixtures, and cabinet work) to be free of defects in materials or workmanship for a period of sixty (60) days from the date of final settlement or first occupancy, whichever comes first [1]. The Builder is obligated to repair or replace these items at no charge within sixty (60) d...
```

### Q-D4: Which documents mention **insurance** and what limits are specified?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.08 |
| Containment | 1.00 |
| Precision | 0.27 |
| Recall | 1.00 |
| F1 Score | 0.42 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 4258 |
| Latency P95 (ms) | 4258 |
| Latency Min (ms) | 4258 |
| Latency Max (ms) | 4258 |

**Run 1 (4258ms):**

```
## Summary

The PROPERTY MANAGEMENT AGREEMENT mentions insurance requirements. Specifically, it obligates the Owner to provide liability insurance coverage for the property with minimum limits of $300,000 for bodily injury and $25,000 for property damage to others. Additionally, the Agent must be named as an additional insured and furnished with a copy of the insurance policy and a certificate of insurance. No insurance requirements or limits are specified in the BUILDERS LIMITED WARRANTY docume...
```

### Q-D5: In the warranty, explain how the "coverage start" is defined and what must happen before coverage ends.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.05 |
| Containment | 0.85 |
| Precision | 0.24 |
| Recall | 0.85 |
| F1 Score | 0.38 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 5100 |
| Latency P95 (ms) | 5100 |
| Latency Min (ms) | 5100 |
| Latency Max (ms) | 5100 |

**Run 1 (5100ms):**

```
## Summary

The "coverage start" for the Builder's Limited Warranty is defined as the earlier of two events: the date of final settlement or the date when the Buyer/Owner first occupies the home [1]. The coverage ends either one (1) year or sixty (60) days after commencement, as applicable, unless otherwise provided in the warranty [1]. Before coverage ends, the Buyer/Owner must send a written letter describing any defect to the Builder by certified mail, return receipt requested, within the app...
```

### Q-D6: Do the purchase contract total price and the invoice total match? If so, what is that amount?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.02 |
| Containment | 0.90 |
| Precision | 0.16 |
| Recall | 0.90 |
| F1 Score | 0.27 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 40958 |
| Latency P95 (ms) | 40958 |
| Latency Min (ms) | 40958 |
| Latency Max (ms) | 40958 |

**Run 1 (40958ms):**

```
## Summary

Yes, the purchase contract total price and the invoice total match. Both documents state the total amount as $29,900.00. The purchase contract specifies a total contract price of $29,900.00, payable in three installments: $20,000.00 upon signing, $7,000.00 upon delivery, and $2,900.00 upon completion [3]. The invoice lists a subtotal, total, and amount due of $29,900.00, with no tax applied [1]. The invoice itemizes the products and services provided, and their combined total equals ...
```

### Q-D7: Which document has the latest explicit date, and what is it?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.14 |
| Containment | 0.74 |
| Precision | 0.33 |
| Recall | 0.74 |
| F1 Score | 0.45 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 4721 |
| Latency P95 (ms) | 4721 |
| Latency Min (ms) | 4721 |
| Latency Max (ms) | 4721 |

**Run 1 (4721ms):**

```
## Summary

The document with the latest explicit date is the "purchase contract," which is signed on 04/30/2025. This date is later than any other explicit date found in the provided documents, including the "HOLDING TANK SERVICING CONTRACT" (2024-06-15), "PROPERTY MANAGEMENT AGREEMENT" (2010-06-15), and "BUILDERS LIMITED WARRANTY" (2010-06-15) [7].

## Key Points

- The "purchase contract" has the latest explicit date: 04/30/2025 [7].
- Other documents contain earlier dates: "HOLDING TANK SERV...
```

### Q-D8: Across the set, which entity appears in the most different documents: `Fabrikam Inc.` or `Contoso Ltd.`?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.13 |
| Containment | 0.66 |
| Precision | 0.50 |
| Recall | 0.66 |
| F1 Score | 0.57 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 7412 |
| Latency P95 (ms) | 7412 |
| Latency Min (ms) | 7412 |
| Latency Max (ms) | 7412 |

**Run 1 (7412ms):**

```
## Summary

Based on the authoritative Entity-Document Map, both Fabrikam Inc. and Contoso Ltd. appear as parties or signatories in the same number of unique documents: four each. The documents in which each entity appears as a party or signatory are: BUILDERS LIMITED WARRANTY, HOLDING TANK SERVICING CONTRACT, PROPERTY MANAGEMENT AGREEMENT, and purchase_contract. Therefore, neither Fabrikam Inc. nor Contoso Ltd. appears in more different documents than the other as a party or signatory [BUILDERS...
```

### Q-D9: Compare the "fees" concepts: which doc has a percentage-based fee structure and which has fixed installment payments?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.07 |
| Containment | 1.00 |
| Precision | 0.23 |
| Recall | 1.00 |
| F1 Score | 0.37 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 7327 |
| Latency P95 (ms) | 7327 |
| Latency Min (ms) | 7327 |
| Latency Max (ms) | 7327 |

**Run 1 (7327ms):**

```
## Summary

The "fees" concepts in the two documents differ in structure. The Property Management Agreement uses a percentage-based fee structure for several services, including a 25% commission on gross revenues for short-term/vacation rentals and a 10% commission on gross revenues for long-term leases, as well as a 10% fee on the total charge for repairs, upgrades, and renovations. It also includes some fixed fees, such as a $35/hour charge for scheduling or escorting contractors, a $75/month ...
```

### Q-D10: List the three different "risk allocation" statements across the set (risk of loss, liability limitations, non-transferability).

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | ❌ |
| Fuzzy Score | 0.11 |
| Containment | 0.94 |
| Precision | 0.35 |
| Recall | 0.94 |
| F1 Score | 0.51 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 5357 |
| Latency P95 (ms) | 5357 |
| Latency Min (ms) | 5357 |
| Latency Max (ms) | 5357 |

**Run 1 (5357ms):**

```
## Summary

The documents contain three distinct "risk allocation" statements: (1) risk of loss is allocated to the contractor until delivery and to the customer thereafter in the purchase contract; (2) liability limitations are set in the property management agreement, which limits the agent's liability except in cases of gross negligence or willful misconduct and requires the owner to indemnify the agent; (3) non-transferability is addressed in both the purchase contract, which restricts assig...
```

### Q-N1: What is the invoice's **bank routing number** for payment?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ✅ PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 2026 |
| Latency P95 (ms) | 2026 |
| Latency Min (ms) | 2026 |
| Latency Max (ms) | 2026 |

**Run 1 (2026ms):**

```
Not found in the provided documents.
```

### Q-N2: What is the invoice’s **IBAN / SWIFT (BIC)** for international payments?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ✅ PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 2025 |
| Latency P95 (ms) | 2025 |
| Latency Min (ms) | 2025 |
| Latency Max (ms) | 2025 |

**Run 1 (2025ms):**

```
Not found in the provided documents.
```

### Q-N3: What is the vendor's **VAT / Tax ID number** on the invoice?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ❌ FAIL |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 5571 |
| Latency P95 (ms) | 5571 |
| Latency Min (ms) | 5571 |
| Latency Max (ms) | 5571 |

**Run 1 (5571ms):**

```
## Summary

The vendor's VAT / Tax ID number does not appear anywhere on the provided invoice from Contoso Lifts LLC. The invoice includes company contact information, itemized charges, and payment instructions, but there is no mention of a VAT, Tax ID, or similar identifier in the available evidence [3].

## Key Points

- The invoice from Contoso Lifts LLC does not display a VAT or Tax ID number [3].
- The document provides company address, phone, and email, but omits any tax identification det...
```

### Q-N5: What is the invoice’s **bank account number** for ACH/wire payments?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ✅ PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 2034 |
| Latency P95 (ms) | 2034 |
| Latency Min (ms) | 2034 |
| Latency Max (ms) | 2034 |

**Run 1 (2034ms):**

```
Not found in the provided documents.
```

### Q-N6: Which documents are governed by the laws of **California**?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ✅ PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 2041 |
| Latency P95 (ms) | 2041 |
| Latency Min (ms) | 2041 |
| Latency Max (ms) | 2041 |

**Run 1 (2041ms):**

```
Not found in the provided documents.
```

### Q-N7: What is the property management Agent's **license number**?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ✅ PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 5273 |
| Latency P95 (ms) | 5273 |
| Latency Min (ms) | 5273 |
| Latency Max (ms) | 5273 |

**Run 1 (5273ms):**

```
## Summary

The property management Agent's license number is not provided in the available Property Management Agreement. The document identifies the Agent as "Walt Flood Realty, a Hawaii sole proprietorship," but does not list any license number for the Agent or its Principal Broker [1].

## Key Points

- The Agent is identified as Walt Flood Realty, a Hawaii sole proprietorship [1].
- No license number for the Agent is stated in the available document [1].

The requested information was not f...
```

### Q-N8: What is the purchase contract’s required **wire transfer / ACH instructions**?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ✅ PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 4489 |
| Latency P95 (ms) | 4489 |
| Latency Min (ms) | 4489 |
| Latency Max (ms) | 4489 |

**Run 1 (4489ms):**

```
## Summary

The purchase contract specifies the total contract price and payment milestones but does not provide any wire transfer or ACH instructions, such as bank account numbers, routing numbers, or payment processing details. No explicit wire transfer or ACH instructions are included in the available document text [1].

## Key Points

- The total contract price is $29,900.00, payable in three installments: $20,000.00 upon signing, $7,000.00 upon delivery, and $2,900.00 upon completion [1].
-...
```

### Q-N9: What is the exact clause about **mold damage** coverage in the warranty?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ✅ PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 2044 |
| Latency P95 (ms) | 2044 |
| Latency Min (ms) | 2044 |
| Latency Max (ms) | 2044 |

**Run 1 (2044ms):**

```
Not found in the provided documents.
```

### Q-N10: What is the invoice **shipping method** (value in "SHIPPED VIA")?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | ✅ PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Citations Jaccard (Min) | 1.00 |
| Evidence Path Jaccard (Min) | 1.00 |
| Latency P50 (ms) | 5310 |
| Latency P95 (ms) | 5310 |
| Latency Min (ms) | 5310 |
| Latency Max (ms) | 5310 |

**Run 1 (5310ms):**

```
## Summary

The invoice from Contoso Lifts LLC includes a table with a column labeled "SHIPPED VIA," which is intended to indicate the shipping method. However, the corresponding cell for "SHIPPED VIA" is left blank in the provided evidence, and no shipping method is specified elsewhere in the document [1].

## Key Points

- The "SHIPPED VIA" field in the invoice is present but contains no value; the shipping method is not specified [1].

Response: The requested information was not found in the ...
```

---

