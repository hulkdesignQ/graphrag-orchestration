# Route 7 (HippoRAG 2) Benchmark

**Timestamp:** 20260226T120257Z

**API Base URL:** `https://graphrag-api.salmonhill-df6033f3.swedencentral.azurecontainerapps.io`

**Group ID:** `test-5pdfs-v2-fix2`

**Force Route:** `hipporag2_search`

**Architecture:** True HippoRAG 2 with passage-node PPR, query-to-triple linking, and recognition memory filtering.

---

## Scenario: route7_hipporag2_r4questions_summary

**Response Type:** `summary`

### Summary Table

| QID | Containment | F1 | Neg Pass | Exact Rate | Min Sim | P50 ms | P95 ms |
|-----|-------------|-----|----------|------------|---------|--------|--------|
| Q-D1 | 0.50 | 0.18 | - | 1.00 | 1.00 | 36596 | 36596 |
| Q-D2 | 0.00 | 0.00 | - | 1.00 | 1.00 | 1977 | 1977 |
| Q-D3 | 0.19 | 0.20 | - | 1.00 | 1.00 | 4808 | 4808 |
| Q-D4 | 0.21 | 0.15 | - | 1.00 | 1.00 | 5210 | 5210 |
| Q-D5 | 0.37 | 0.29 | - | 1.00 | 1.00 | 4217 | 4217 |
| Q-D6 | 0.30 | 0.07 | - | 1.00 | 1.00 | 6078 | 6078 |
| Q-D7 | 0.57 | 0.33 | - | 1.00 | 1.00 | 4379 | 4379 |
| Q-D8 | 0.50 | 0.40 | - | 1.00 | 1.00 | 5718 | 5718 |
| Q-D9 | 0.40 | 0.22 | - | 1.00 | 1.00 | 5674 | 5674 |
| Q-D10 | 0.42 | 0.22 | - | 1.00 | 1.00 | 5902 | 5902 |
| Q-N1 | - | - | PASS | 1.00 | 1.00 | 2934 | 2934 |
| Q-N2 | - | - | PASS | 1.00 | 1.00 | 1949 | 1949 |
| Q-N3 | - | - | PASS | 1.00 | 1.00 | 1961 | 1961 |
| Q-N5 | - | - | PASS | 1.00 | 1.00 | 2000 | 2000 |
| Q-N6 | - | - | PASS | 1.00 | 1.00 | 1958 | 1958 |
| Q-N7 | - | - | PASS | 1.00 | 1.00 | 4600 | 4600 |
| Q-N8 | - | - | PASS | 1.00 | 1.00 | 4002 | 4002 |
| Q-N9 | - | - | PASS | 1.00 | 1.00 | 2138 | 2138 |
| Q-N10 | - | - | PASS | 1.00 | 1.00 | 4596 | 4596 |

**Positive questions avg containment:** 0.35  
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
| Containment | 0.50 |
| Precision | 0.11 |
| Recall | 0.50 |
| F1 Score | 0.18 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 36596 |
| Latency P95 (ms) | 36596 |

**Run 1 (36596ms):**

```
## Summary

If an emergency defect occurs under the Builders Limited Warranty (such as a burst pipe), the required notification channel is immediate telephone notification to the Builder, followed by written notice within three (3) days after discovery of the defect. Failure to provide timely notice may result in the Builder not being responsible for damages that could have been avoided by prompt notification, and may also affect the Owner's rights under the warranty [4].

## Key Points

- Emerg...
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
| Latency P50 (ms) | 1977 |
| Latency P95 (ms) | 1977 |

**Run 1 (1977ms):**

```
Not found in the provided documents.
```

#### Q-D3: Compare "time windows" across the set: list all explicit day-based timeframes.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.03 |
| Containment | 0.19 |
| Precision | 0.22 |
| Recall | 0.19 |
| F1 Score | 0.20 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4808 |
| Latency P95 (ms) | 4808 |

**Run 1 (4808ms):**

```
## Summary

Across the available documents, explicit day-based timeframes ("time windows") are limited. The "BUILDERS LIMITED WARRANTY" specifies a warranty period of one (1) year from the start date, which is a clear day-based timeframe for the builder's obligations regarding the construction or purchase of a home [1]. No other documents in the provided evidence context contain explicit day-based timeframes.

## Key Points

- The builder warrants for a period of one (1) year from the start date...
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
| Latency P50 (ms) | 5210 |
| Latency P95 (ms) | 5210 |

**Run 1 (5210ms):**

```
## Summary

Based on the available documents, the PROPERTY MANAGEMENT AGREEMENT mentions insurance. However, the provided evidence does not specify any insurance limits or detailed insurance requirements. No other documents in the evidence context explicitly mention insurance or specify insurance limits.

## Key Points

- The PROPERTY MANAGEMENT AGREEMENT mentions insurance, but no specific insurance limits are provided in the available excerpt [1].
- No other documents in the evidence context m...
```

#### Q-D5: In the warranty, explain how the "coverage start" is defined and what must happen before coverage ends.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.05 |
| Containment | 0.37 |
| Precision | 0.24 |
| Recall | 0.37 |
| F1 Score | 0.29 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4217 |
| Latency P95 (ms) | 4217 |

**Run 1 (4217ms):**

```
## Summary

In the Builders Limited Warranty, the "coverage start" is defined as beginning with the start of the one (1) year warranty period, which is tied to the construction or purchase agreement for the home. Coverage under this warranty ends after the expiration of the one (1) year period from the coverage start date [4].

## Key Points

- The warranty coverage starts at the beginning of the one (1) year period associated with the construction or purchase agreement for the home [4].
- Cover...
```

#### Q-D6: Do the purchase contract total price and the invoice total match? If so, what is that amount?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.01 |
| Containment | 0.30 |
| Precision | 0.04 |
| Recall | 0.30 |
| F1 Score | 0.07 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 6078 |
| Latency P95 (ms) | 6078 |

**Run 1 (6078ms):**

```
## Summary

The available documents do not provide the total price from either the purchase contract or the invoice. The invoice document includes header information such as invoice number, customer ID, date, and some shipping and sales details, but the section listing quantities, descriptions, and unit prices is incomplete and does not display any total amount. Similarly, the purchase contract describes the items and services to be provided but does not specify any total price or payment amount...
```

#### Q-D7: Which document has the latest explicit date, and what is it?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.13 |
| Containment | 0.57 |
| Precision | 0.24 |
| Recall | 0.57 |
| F1 Score | 0.33 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4379 |
| Latency P95 (ms) | 4379 |

**Run 1 (4379ms):**

```
## Summary

The document with the latest explicit date is the "HOLDING TANK SERVICING CONTRACT," which is dated 2024-06-15. None of the other documents in the provided evidence context contain an explicit date that is later than this.

## Key Points

- The "HOLDING TANK SERVICING CONTRACT" is explicitly dated 2024-06-15 [1].
- The "PROPERTY MANAGEMENT AGREEMENT" references a term beginning date but does not specify an explicit date [2].
- The "BUILDERS LIMITED WARRANTY" does not contain an expli...
```

#### Q-D8: Across the set, which entity appears in the most different documents: `Fabrikam Inc.` or `Contoso Ltd.`?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.08 |
| Containment | 0.50 |
| Precision | 0.33 |
| Recall | 0.50 |
| F1 Score | 0.40 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5718 |
| Latency P95 (ms) | 5718 |

**Run 1 (5718ms):**

```
## Summary

Based on the authoritative Entity-Document Map, Fabrikam Inc. appears as a direct party or signatory in more unique documents than Contoso Ltd. Specifically, Fabrikam Inc. is a party to four different documents: BUILDERS LIMITED WARRANTY, purchase_contract, HOLDING TANK SERVICING CONTRACT, and PROPERTY MANAGEMENT AGREEMENT. In contrast, Contoso Ltd. is a party to three documents: BUILDERS LIMITED WARRANTY, HOLDING TANK SERVICING CONTRACT, and PROPERTY MANAGEMENT AGREEMENT. Only entri...
```

#### Q-D9: Compare the "fees" concepts: which doc has a percentage-based fee structure and which has fixed installment payments?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.08 |
| Containment | 0.40 |
| Precision | 0.15 |
| Recall | 0.40 |
| F1 Score | 0.22 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5674 |
| Latency P95 (ms) | 5674 |

**Run 1 (5674ms):**

```
## Summary

Based on the available evidence, the "PROPERTY MANAGEMENT AGREEMENT" includes a percentage-based fee structure, as it is standard for property management contracts to compensate the agent with a percentage of the rental income collected, though the exact percentage is not specified in the provided excerpt [1]. The "purchase_contract" refers to an initial payment and implies fixed installment payments for the furnishing and installation of equipment, but does not mention any percentag...
```

#### Q-D10: List the three different "risk allocation" statements across the set (risk of loss, liability limitations, non-transferability).

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.03 |
| Containment | 0.42 |
| Precision | 0.15 |
| Recall | 0.42 |
| F1 Score | 0.22 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5902 |
| Latency P95 (ms) | 5902 |

**Run 1 (5902ms):**

```
## Summary

Across the provided documents, three distinct "risk allocation" statements can be identified: (1) risk of loss, (2) liability limitations, and (3) non-transferability. However, the available evidence contains only partial or implied references to these categories, with explicit statements primarily regarding non-transferability. The purchase contract and property management agreement do not contain explicit risk of loss or liability limitation clauses. The Builders Limited Warranty d...
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
| Latency P50 (ms) | 2934 |
| Latency P95 (ms) | 2934 |

**Run 1 (2934ms):**

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
| Latency P50 (ms) | 1949 |
| Latency P95 (ms) | 1949 |

**Run 1 (1949ms):**

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
| Latency P50 (ms) | 1961 |
| Latency P95 (ms) | 1961 |

**Run 1 (1961ms):**

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
| Latency P50 (ms) | 2000 |
| Latency P95 (ms) | 2000 |

**Run 1 (2000ms):**

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
| Latency P50 (ms) | 1958 |
| Latency P95 (ms) | 1958 |

**Run 1 (1958ms):**

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
| Latency P50 (ms) | 4600 |
| Latency P95 (ms) | 4600 |

**Run 1 (4600ms):**

```
## Summary

The property management Agent's license number is not provided in the available documents. The PROPERTY MANAGEMENT AGREEMENT identifies the Agent as "Walt Flood Realty, a Hawaii sole proprietorship," but does not specify a license number for the Agent or agency [1].

## Key Points

- The PROPERTY MANAGEMENT AGREEMENT names Walt Flood Realty as the Agent but does not include a license number [1].

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
| Latency P50 (ms) | 4002 |
| Latency P95 (ms) | 4002 |

**Run 1 (4002ms):**

```
## Summary

The purchase contract does not provide any specific wire transfer or ACH instructions, such as bank account numbers, routing numbers, or payment remittance details. The available documents do not include explicit instructions for making payments via wire transfer or ACH, nor do they specify any related banking information or procedures [1][2][3].

## Key Points

- The contract does not state any wire transfer or ACH instructions, including bank account or routing numbers [1][2][3].
-...
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
| Latency P50 (ms) | 2138 |
| Latency P95 (ms) | 2138 |

**Run 1 (2138ms):**

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
| Latency P50 (ms) | 4596 |
| Latency P95 (ms) | 4596 |

**Run 1 (4596ms):**

```
## Summary

The invoice does not specify a shipping method; the "SHIPPED VIA" field in the provided table is blank and contains no value [1].

## Key Points

- The "SHIPPED VIA" (shipping method) field on the invoice is blank and does not contain any information [1].
```

---

