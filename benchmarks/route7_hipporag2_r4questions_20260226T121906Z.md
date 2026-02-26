# Route 7 (HippoRAG 2) Benchmark

**Timestamp:** 20260226T121906Z

**API Base URL:** `http://localhost:8000`

**Group ID:** `test-5pdfs-v2-fix2`

**Force Route:** `hipporag2_search`

**Architecture:** True HippoRAG 2 with passage-node PPR, query-to-triple linking, and recognition memory filtering.

---

## Scenario: route7_hipporag2_r4questions_summary

**Response Type:** `summary`

### Summary Table

| QID | Containment | F1 | Neg Pass | Exact Rate | Min Sim | P50 ms | P95 ms |
|-----|-------------|-----|----------|------------|---------|--------|--------|
| Q-D1 | 0.94 | 0.38 | - | 1.00 | 1.00 | 4006 | 4006 |
| Q-D2 | 0.83 | 0.18 | - | 1.00 | 1.00 | 2982 | 2982 |
| Q-D3 | 0.43 | 0.31 | - | 1.00 | 1.00 | 5335 | 5335 |
| Q-D4 | 1.00 | 0.48 | - | 1.00 | 1.00 | 4394 | 4394 |
| Q-D5 | 0.78 | 0.37 | - | 1.00 | 1.00 | 3983 | 3983 |
| Q-D6 | 0.90 | 0.25 | - | 1.00 | 1.00 | 4425 | 4425 |
| Q-D7 | 1.00 | 0.51 | - | 1.00 | 1.00 | 3544 | 3544 |
| Q-D8 | 0.50 | 0.44 | - | 1.00 | 1.00 | 6783 | 6783 |
| Q-D9 | 0.92 | 0.35 | - | 1.00 | 1.00 | 4595 | 4595 |
| Q-D10 | 0.97 | 0.41 | - | 1.00 | 1.00 | 5380 | 5380 |
| Q-N1 | - | - | PASS | 1.00 | 1.00 | 1259 | 1259 |
| Q-N2 | - | - | PASS | 1.00 | 1.00 | 1139 | 1139 |
| Q-N3 | - | - | PASS | 1.00 | 1.00 | 3752 | 3752 |
| Q-N5 | - | - | PASS | 1.00 | 1.00 | 1094 | 1094 |
| Q-N6 | - | - | PASS | 1.00 | 1.00 | 1152 | 1152 |
| Q-N7 | - | - | PASS | 1.00 | 1.00 | 3771 | 3771 |
| Q-N8 | - | - | PASS | 1.00 | 1.00 | 4636 | 4636 |
| Q-N9 | - | - | PASS | 1.00 | 1.00 | 1119 | 1119 |
| Q-N10 | - | - | PASS | 1.00 | 1.00 | 20617 | 20617 |

**Positive questions avg containment:** 0.83  
**Positive questions avg F1:** 0.37  

**Negative tests passed:** 9/9  

### Per-Question Detail

#### Q-D1: If an emergency defect occurs under the warranty (e.g., burst pipe), what is the required notification channel and consequence of delay?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.00 |
| Containment | 0.94 |
| Precision | 0.23 |
| Recall | 0.94 |
| F1 Score | 0.38 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4006 |
| Latency P95 (ms) | 4006 |

**Run 1 (4006ms):**

```
## Summary

If an emergency defect occurs under the warranty, such as a burst pipe, the Buyer/Owner is required to immediately notify the Builder by telephone using the emergency number provided. Only emergency reports are accepted by phone. Failure to promptly notify the Builder of an emergency relieves the Builder of all liability for replacement, repair, and all other damages related to the defect [1][2].

## Key Points

- The Buyer/Owner must immediately telephone the Builder in the event of...
```

#### Q-D2: In the property management agreement, what happens to confirmed reservations if the agreement is terminated or the property is sold?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
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
| Latency P50 (ms) | 2982 |
| Latency P95 (ms) | 2982 |

**Run 1 (2982ms):**

```
## Summary

If the property management agreement is terminated or the property is sold, the Owner is required to honor all confirmed reservations. Additionally, termination of the agreement does not invalidate any existing rental agreements made by the Agent on the Owner's behalf. The Owner remains responsible for completing all obligations or expenses incurred under the agreement by the Agent, even after termination [1][2].

## Key Points

- Upon termination of the agreement or sale of the prop...
```

#### Q-D3: Compare "time windows" across the set: list all explicit day-based timeframes.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.04 |
| Containment | 0.43 |
| Precision | 0.24 |
| Recall | 0.43 |
| F1 Score | 0.31 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5335 |
| Latency P95 (ms) | 5335 |

**Run 1 (5335ms):**

```
## Summary

Across the provided documents, the explicit day-based timeframes ("time windows") are as follows: The Builder's Limited Warranty covers certain items for a period of sixty (60) days and other items for a period of one (1) year, with all claims required to be made in writing within these respective periods. The Property Management Agreement specifies an initial period of twelve months (equivalent to 365 days) and automatic renewal for successive one-year terms. No other explicit day-b...
```

#### Q-D4: Which documents mention **insurance** and what limits are specified?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.21 |
| Containment | 1.00 |
| Precision | 0.32 |
| Recall | 1.00 |
| F1 Score | 0.48 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4394 |
| Latency P95 (ms) | 4394 |

**Run 1 (4394ms):**

```
## Summary

The PROPERTY MANAGEMENT AGREEMENT mentions insurance and specifies that the Owner must provide liability insurance coverage for the property with minimum limits of $300,000 for bodily injury and $25,000 for property damage to others. Additionally, the Agent must be named as an additional insured and furnished with a copy of the insurance policy and a certificate of insurance. The BUILDERS LIMITED WARRANTY does not mention insurance or specify any insurance limits in the provided exce...
```

#### Q-D5: In the warranty, explain how the "coverage start" is defined and what must happen before coverage ends.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.06 |
| Containment | 0.78 |
| Precision | 0.24 |
| Recall | 0.78 |
| F1 Score | 0.37 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3983 |
| Latency P95 (ms) | 3983 |

**Run 1 (3983ms):**

```
## Summary

The "coverage start" for the Builder's Limited Warranty is defined as the earlier of two events: the date of final settlement or the date when the Buyer/Owner first occupies the home [1]. The coverage ends either one (1) year or sixty (60) days after commencement, as applicable, unless otherwise provided in the warranty [1]. Before coverage ends, the Buyer/Owner must submit any claims in writing to the Builder, describing the defect and sending the letter by certified mail return rec...
```

#### Q-D6: Do the purchase contract total price and the invoice total match? If so, what is that amount?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.05 |
| Containment | 0.90 |
| Precision | 0.14 |
| Recall | 0.90 |
| F1 Score | 0.25 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4425 |
| Latency P95 (ms) | 4425 |

**Run 1 (4425ms):**

```
## Summary

Yes, the purchase contract total price and the invoice total match. Both the purchase contract and the invoice state a total amount of $29,900.00 as the agreed price for the goods and services provided. The purchase contract specifies a "Total contract price is $29,900.00, payable in 3 installments" [3], and the invoice lists a "TOTAL" and "AMOUNT DUE" of $29,900.00 [1][2].

## Key Points

- The purchase contract states the total contract price is $29,900.00, payable in three install...
```

#### Q-D7: Which document has the latest explicit date, and what is it?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.08 |
| Containment | 1.00 |
| Precision | 0.34 |
| Recall | 1.00 |
| F1 Score | 0.51 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3544 |
| Latency P95 (ms) | 3544 |

**Run 1 (3544ms):**

```
## Summary

The document with the latest explicit date is the "purchase contract," which is signed on 04/30/2025. This is the most recent date mentioned among all the provided documents, surpassing other dates such as 2024-06-15 in the "HOLDING TANK SERVICING CONTRACT" and earlier dates in other documents [7].

## Key Points

- The "purchase contract" has the latest explicit date: Signed date: 04/30/2025 [7].
- The next most recent date is 2024-06-15 in the "HOLDING TANK SERVICING CONTRACT" [1]....
```

#### Q-D8: Across the set, which entity appears in the most different documents: `Fabrikam Inc.` or `Contoso Ltd.`?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.08 |
| Containment | 0.50 |
| Precision | 0.39 |
| Recall | 0.50 |
| F1 Score | 0.44 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 6783 |
| Latency P95 (ms) | 6783 |

**Run 1 (6783ms):**

```
## Summary

Based on the authoritative Entity-Document Map, Fabrikam Inc. appears as a party or signatory in more unique documents than Contoso Ltd. Specifically, Fabrikam Inc. is a party to four different documents: BUILDERS LIMITED WARRANTY, purchase_contract, HOLDING TANK SERVICING CONTRACT, and PROPERTY MANAGEMENT AGREEMENT. In contrast, Contoso Ltd. is a party or signatory in three documents: BUILDERS LIMITED WARRANTY, PROPERTY MANAGEMENT AGREEMENT, and HOLDING TANK SERVICING CONTRACT. Ther...
```

#### Q-D9: Compare the "fees" concepts: which doc has a percentage-based fee structure and which has fixed installment payments?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.07 |
| Containment | 0.92 |
| Precision | 0.21 |
| Recall | 0.92 |
| F1 Score | 0.35 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4595 |
| Latency P95 (ms) | 4595 |

**Run 1 (4595ms):**

```
## Summary

The "Property Management Agreement" uses a percentage-based fee structure for its main management services, charging 25% of gross revenues for short-term/vacation rentals (less than 180 days) and 10% of gross revenues for long-term leases (more than 180 days). It also charges 10% on the total charge for repairs, upgrades, and renovations, and includes other fixed fees such as $35/hour for scheduling/escorting contractors, $75/month for advertising, $50/month for administration/accoun...
```

#### Q-D10: List the three different "risk allocation" statements across the set (risk of loss, liability limitations, non-transferability).

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.02 |
| Containment | 0.97 |
| Precision | 0.26 |
| Recall | 0.97 |
| F1 Score | 0.41 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5380 |
| Latency P95 (ms) | 5380 |

**Run 1 (5380ms):**

```
## Summary

The three different "risk allocation" statements across the provided documents are: (1) risk of loss, (2) liability limitations, and (3) non-transferability. The purchase contract specifies that the contractor holds the risk of loss until delivery, after which the customer assumes the risk. Liability limitations are addressed in both the Builders Limited Warranty and the Property Management Agreement, with disclaimers of certain liabilities and requirements for indemnification and in...
```

#### Q-N1: What is the invoice's **bank routing number** for payment?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 1259 |
| Latency P95 (ms) | 1259 |

**Run 1 (1259ms):**

```
Not found in the provided documents.
```

#### Q-N2: What is the invoice’s **IBAN / SWIFT (BIC)** for international payments?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 1139 |
| Latency P95 (ms) | 1139 |

**Run 1 (1139ms):**

```
Not found in the provided documents.
```

#### Q-N3: What is the vendor's **VAT / Tax ID number** on the invoice?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3752 |
| Latency P95 (ms) | 3752 |

**Run 1 (3752ms):**

```
## Summary

The vendor's VAT / Tax ID number does not appear anywhere on the provided invoice or in any of the available documents. The invoice from Contoso Lifts LLC includes company contact information, invoice details, and payment instructions, but there is no mention of a VAT, Tax ID, or similar tax identification number for the vendor [3].

## Key Points

- The invoice from Contoso Lifts LLC does not list a VAT or Tax ID number for the vendor [3].
- No other document in the evidence context...
```

#### Q-N5: What is the invoice’s **bank account number** for ACH/wire payments?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 1094 |
| Latency P95 (ms) | 1094 |

**Run 1 (1094ms):**

```
Not found in the provided documents.
```

#### Q-N6: Which documents are governed by the laws of **California**?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 1152 |
| Latency P95 (ms) | 1152 |

**Run 1 (1152ms):**

```
Not found in the provided documents.
```

#### Q-N7: What is the property management Agent's **license number**?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3771 |
| Latency P95 (ms) | 3771 |

**Run 1 (3771ms):**

```
## Summary

The property management Agent named in the agreement is Walt Flood Realty, a Hawaii sole proprietorship. However, the Agent's **license number** is not provided anywhere in the available document. The agreement details the parties, property address, management terms, fees, and obligations, but does not include any license number for the Agent [1].

## Key Points

- The Agent is Walt Flood Realty, a Hawaii sole proprietorship [1].
- The Agent's license number is not listed in the avai...
```

#### Q-N8: What is the purchase contract’s required **wire transfer / ACH instructions**?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4636 |
| Latency P95 (ms) | 4636 |

**Run 1 (4636ms):**

```
## Summary

The available documents do not provide specific wire transfer or ACH instructions, such as bank account numbers, routing numbers, or payment remittance details. The purchase contract and invoice specify payment amounts, milestones, and that payments can be made by check to "Contoso Lifts LLC" or via an online portal (https://ww.contosolifts.com/portal/pay), but do not include explicit wire transfer or ACH instructions [1][10].

## Key Points

- The contract price is $29,900.00, payab...
```

#### Q-N9: What is the exact clause about **mold damage** coverage in the warranty?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 1119 |
| Latency P95 (ms) | 1119 |

**Run 1 (1119ms):**

```
Not found in the provided documents.
```

#### Q-N10: What is the invoice **shipping method** (value in "SHIPPED VIA")?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 20617 |
| Latency P95 (ms) | 20617 |

**Run 1 (20617ms):**

```
## Summary

The invoice does not specify a shipping method; the "SHIPPED VIA" field in the invoice table is left blank, and no other part of the document provides a value for the shipping method or carrier used for delivery [1].

## Key Points

- The "SHIPPED VIA" field in the invoice table is empty; no shipping method is listed [1].
- No other evidence context provides a shipping method or carrier for this invoice [1].

Response: The requested information was not found in the available document...
```

---

