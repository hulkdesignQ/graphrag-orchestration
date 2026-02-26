# Route 7 (HippoRAG 2) Benchmark

**Timestamp:** 20260226T122606Z

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
| Q-D1 | 0.38 | 0.14 | - | 1.00 | 1.00 | 35166 | 35166 |
| Q-D2 | 0.00 | 0.00 | - | 1.00 | 1.00 | 1192 | 1192 |
| Q-D3 | 0.26 | 0.26 | - | 1.00 | 1.00 | 5685 | 5685 |
| Q-D4 | 0.21 | 0.15 | - | 1.00 | 1.00 | 3628 | 3628 |
| Q-D5 | 0.37 | 0.26 | - | 1.00 | 1.00 | 3072 | 3072 |
| Q-D6 | 0.20 | 0.05 | - | 1.00 | 1.00 | 3518 | 3518 |
| Q-D7 | 0.35 | 0.23 | - | 1.00 | 1.00 | 3558 | 3558 |
| Q-D8 | 0.50 | 0.42 | - | 1.00 | 1.00 | 3802 | 3802 |
| Q-D9 | 0.64 | 0.38 | - | 1.00 | 1.00 | 3989 | 3989 |
| Q-D10 | 0.52 | 0.22 | - | 1.00 | 1.00 | 4027 | 4027 |
| Q-N1 | - | - | PASS | 1.00 | 1.00 | 1213 | 1213 |
| Q-N2 | - | - | PASS | 1.00 | 1.00 | 1089 | 1089 |
| Q-N3 | - | - | PASS | 1.00 | 1.00 | 1133 | 1133 |
| Q-N5 | - | - | PASS | 1.00 | 1.00 | 1179 | 1179 |
| Q-N6 | - | - | PASS | 1.00 | 1.00 | 1014 | 1014 |
| Q-N7 | - | - | PASS | 1.00 | 1.00 | 3202 | 3202 |
| Q-N8 | - | - | PASS | 1.00 | 1.00 | 3260 | 3260 |
| Q-N9 | - | - | PASS | 1.00 | 1.00 | 1509 | 1509 |
| Q-N10 | - | - | PASS | 1.00 | 1.00 | 2885 | 2885 |

**Positive questions avg containment:** 0.34  
**Positive questions avg F1:** 0.21  

**Negative tests passed:** 9/9  

### Per-Question Detail

#### Q-D1: If an emergency defect occurs under the warranty (e.g., burst pipe), what is the required notification channel and consequence of delay?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.02 |
| Containment | 0.38 |
| Precision | 0.09 |
| Recall | 0.38 |
| F1 Score | 0.14 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 35166 |
| Latency P95 (ms) | 35166 |

**Run 1 (35166ms):**

```
## Summary

If an emergency defect occurs under the Builders Limited Warranty (such as a burst pipe), the Buyer/Owner is required to notify the Builder of the defect. The specific notification channel (e.g., phone, email, written notice) is not explicitly stated in the available evidence, but prompt notification is implied as necessary for warranty claims. Delay in notification may result in the Builder not being obligated to remedy the defect, as timely reporting is typically a condition for wa...
```

#### Q-D2: In the property management agreement, what happens to confirmed reservations if the agreement is terminated or the property is sold?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.25 |
| Containment | 0.00 |
| Precision | 0.00 |
| Recall | 0.00 |
| F1 Score | 0.00 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 1192 |
| Latency P95 (ms) | 1192 |

**Run 1 (1192ms):**

```
Not found in the provided documents.
```

#### Q-D3: Compare "time windows" across the set: list all explicit day-based timeframes.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.04 |
| Containment | 0.26 |
| Precision | 0.27 |
| Recall | 0.26 |
| F1 Score | 0.26 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5685 |
| Latency P95 (ms) | 5685 |

**Run 1 (5685ms):**

```
## Summary

Across the provided documents, explicit day-based timeframes are as follows: The Builders Limited Warranty specifies a warranty period of "one (1) year" from the start date for the construction or purchase of a home [1]. The Property Management Agreement establishes an initial term of "twelve months" beginning on the agreement's start date [3]. The Holding Tank Servicing Contract includes a contract date of "2024-06-15" but does not specify a day-based timeframe for obligations or se...
```

#### Q-D4: Which documents mention **insurance** and what limits are specified?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.09 |
| Containment | 0.21 |
| Precision | 0.11 |
| Recall | 0.21 |
| F1 Score | 0.15 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3628 |
| Latency P95 (ms) | 3628 |

**Run 1 (3628ms):**

```
## Summary

Based on the available documents, the PROPERTY MANAGEMENT AGREEMENT mentions insurance. However, the provided evidence does not specify any insurance limits or detailed requirements. No other documents in the evidence context explicitly mention insurance or specify insurance limits.

## Key Points

- The PROPERTY MANAGEMENT AGREEMENT mentions insurance, but no specific insurance limits are provided in the available excerpt [1].
- No other documents in the evidence context mention ins...
```

#### Q-D5: In the warranty, explain how the "coverage start" is defined and what must happen before coverage ends.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.05 |
| Containment | 0.37 |
| Precision | 0.20 |
| Recall | 0.37 |
| F1 Score | 0.26 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3072 |
| Latency P95 (ms) | 3072 |

**Run 1 (3072ms):**

```
## Summary

In the "BUILDERS LIMITED WARRANTY," the coverage start is defined as beginning with the start of the one (1) year warranty period, which is tied to the construction or purchase agreement for the home. Coverage ends after the expiration of this one-year period from the defined start date. No additional conditions for ending coverage are specified beyond the passage of this one-year period from the start date [4].

## Key Points

- The warranty coverage starts at the beginning of a one...
```

#### Q-D6: Do the purchase contract total price and the invoice total match? If so, what is that amount?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.01 |
| Containment | 0.20 |
| Precision | 0.03 |
| Recall | 0.20 |
| F1 Score | 0.05 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3518 |
| Latency P95 (ms) | 3518 |

**Run 1 (3518ms):**

```
## Summary

The available documents do not provide the total price from either the purchase contract or the invoice. The invoice document includes header information and some table headers but does not display any line items or total amounts. Similarly, the purchase contract describes the items and services to be provided but does not specify any total price or payment amount. Therefore, it is not possible to determine whether the purchase contract total price and the invoice total match, nor wh...
```

#### Q-D7: Which document has the latest explicit date, and what is it?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.12 |
| Containment | 0.35 |
| Precision | 0.17 |
| Recall | 0.35 |
| F1 Score | 0.23 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3558 |
| Latency P95 (ms) | 3558 |

**Run 1 (3558ms):**

```
## Summary

The document with the latest explicit date is the "HOLDING TANK SERVICING CONTRACT," which is dated 2024-06-15. No other document in the provided evidence contains a later explicit date [1].

## Key Points

- The "HOLDING TANK SERVICING CONTRACT" is dated 2024-06-15, making it the document with the latest explicit date among those provided [1].
- Other documents either do not contain explicit dates or have incomplete date information [2][3][4][6].
```

#### Q-D8: Across the set, which entity appears in the most different documents: `Fabrikam Inc.` or `Contoso Ltd.`?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.07 |
| Containment | 0.50 |
| Precision | 0.37 |
| Recall | 0.50 |
| F1 Score | 0.42 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3802 |
| Latency P95 (ms) | 3802 |

**Run 1 (3802ms):**

```
## Summary

Based on the authoritative Entity-Document Map, Fabrikam Inc. appears as a direct party or signatory in more unique documents than Contoso Ltd. Specifically, Fabrikam Inc. is a party to four different documents: BUILDERS LIMITED WARRANTY, purchase_contract, HOLDING TANK SERVICING CONTRACT, and PROPERTY MANAGEMENT AGREEMENT. In contrast, Contoso Ltd. is a party to only two documents: BUILDERS LIMITED WARRANTY and PROPERTY MANAGEMENT AGREEMENT [N].

## Key Points

- Fabrikam Inc. is a ...
```

#### Q-D9: Compare the "fees" concepts: which doc has a percentage-based fee structure and which has fixed installment payments?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.11 |
| Containment | 0.64 |
| Precision | 0.27 |
| Recall | 0.64 |
| F1 Score | 0.38 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3989 |
| Latency P95 (ms) | 3989 |

**Run 1 (3989ms):**

```
## Summary

The "Property Management Agreement" specifies a percentage-based fee structure, where the agent receives a commission of twenty five percent (25%) of the gross revenues for management services related to short term and/or vacation rentals, and ten percent (10%) of the gross revenues for other management services. The "purchase contract" does not mention any percentage-based fees or fixed installment payments; it only references an initial payment but does not specify a fixed installm...
```

#### Q-D10: List the three different "risk allocation" statements across the set (risk of loss, liability limitations, non-transferability).

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.02 |
| Containment | 0.52 |
| Precision | 0.14 |
| Recall | 0.52 |
| F1 Score | 0.22 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4027 |
| Latency P95 (ms) | 4027 |

**Run 1 (4027ms):**

```
## Summary

Across the provided documents, three distinct "risk allocation" statements are identified: (1) risk of loss, (2) liability limitations, and (3) non-transferability. However, the available evidence contains only partial or implied references to these categories, with explicit statements largely absent or fragmentary. The purchase contract, builders limited warranty, and property management agreement each address risk allocation in different ways, though none provide comprehensive or e...
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
| Latency P50 (ms) | 1213 |
| Latency P95 (ms) | 1213 |

**Run 1 (1213ms):**

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
| Latency P50 (ms) | 1089 |
| Latency P95 (ms) | 1089 |

**Run 1 (1089ms):**

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
| Latency P50 (ms) | 1133 |
| Latency P95 (ms) | 1133 |

**Run 1 (1133ms):**

```
Not found in the provided documents.
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
| Latency P50 (ms) | 1179 |
| Latency P95 (ms) | 1179 |

**Run 1 (1179ms):**

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
| Latency P50 (ms) | 1014 |
| Latency P95 (ms) | 1014 |

**Run 1 (1014ms):**

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
| Latency P50 (ms) | 3202 |
| Latency P95 (ms) | 3202 |

**Run 1 (3202ms):**

```
## Summary

The property management Agent's license number is not provided in the available documents. The PROPERTY MANAGEMENT AGREEMENT identifies the Agent as "Walt Flood Realty, a Hawaii sole proprietorship," but does not specify a license number for the Agent [1].

## Key Points

- The PROPERTY MANAGEMENT AGREEMENT names Walt Flood Realty as the Agent, but does not include a license number [1].

Response: The requested information was not found in the available documents.
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
| Latency P50 (ms) | 3260 |
| Latency P95 (ms) | 3260 |

**Run 1 (3260ms):**

```
## Summary

The available documents do not provide specific wire transfer or ACH instructions, such as bank account numbers, routing numbers, or payment remittance details. While the purchase contract and invoice reference payment terms (e.g., "Due on contract signing"), they do not include the required wire transfer or ACH instructions necessary to complete an electronic payment [1][4].

## Key Points

- The purchase contract and invoice reference payment terms but do not specify wire transfer ...
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
| Latency P50 (ms) | 1509 |
| Latency P95 (ms) | 1509 |

**Run 1 (1509ms):**

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
| Latency P50 (ms) | 2885 |
| Latency P95 (ms) | 2885 |

**Run 1 (2885ms):**

```
## Summary

The invoice does not specify a shipping method; the "SHIPPED VIA" field in the invoice table is left blank, and there is no other mention of a shipping method in the available documents [1].

## Key Points

- The "SHIPPED VIA" field on the invoice is blank; no shipping method is provided [1].
- No other document in the evidence context specifies a shipping method for this invoice.
```

---

