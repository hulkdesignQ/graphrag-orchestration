# Route 7 (HippoRAG 2) Benchmark

**Timestamp:** 20260308T163511Z

**API Base URL:** `http://localhost:8000`

**Group ID:** `test-5pdfs-v2-fix2`

**Force Route:** `hipporag2_search`

**Architecture:** True HippoRAG 2 with passage-node PPR, query-to-triple linking, and recognition memory filtering.

---

## Scenario: route7_hipporag2_r3questions_summary

**Response Type:** `summary`

### Summary Table

| QID | Containment | F1 | Neg Pass | Exact Rate | Min Sim | P50 ms | P95 ms |
|-----|-------------|-----|----------|------------|---------|--------|--------|
| Q-G1 | 0.93 | 0.52 | - | 0.33 | 0.94 | 5847 | 67585 |
| Q-G2 | 0.94 | 0.30 | - | 0.33 | 0.52 | 4177 | 4445 |
| Q-G3 | 0.82 | 0.32 | - | 0.33 | 0.89 | 7530 | 7626 |
| Q-G4 | 0.88 | 0.23 | - | 0.33 | 0.53 | 7288 | 8354 |
| Q-G5 | 0.50 | 0.08 | - | 0.33 | 0.21 | 6938 | 8869 |
| Q-G6 | 0.73 | 0.44 | - | 0.33 | 0.83 | 5797 | 6921 |
| Q-G7 | 0.91 | 0.42 | - | 0.33 | 0.27 | 4647 | 4931 |
| Q-G8 | 0.82 | 0.44 | - | 0.33 | 0.98 | 5763 | 34875 |
| Q-G9 | 0.61 | 0.46 | - | 0.33 | 0.80 | 3645 | 3653 |
| Q-G10 | 0.57 | 0.27 | - | 0.33 | 0.80 | 4608 | 34866 |
| Q-N1 | - | - | PASS | 1.00 | 1.00 | 3099 | 3233 |
| Q-N2 | - | - | PASS | 1.00 | 1.00 | 3079 | 33515 |
| Q-N3 | - | - | PASS | 1.00 | 1.00 | 3076 | 3121 |
| Q-N5 | - | - | PASS | 1.00 | 1.00 | 2853 | 33557 |
| Q-N6 | - | - | PASS | 1.00 | 1.00 | 3026 | 34019 |
| Q-N7 | - | - | PASS | 1.00 | 1.00 | 2727 | 2806 |
| Q-N8 | - | - | PASS | 0.67 | 0.99 | 2844 | 33599 |
| Q-N9 | - | - | PASS | 1.00 | 1.00 | 2932 | 2944 |
| Q-N10 | - | - | PASS | 1.00 | 1.00 | 2801 | 33606 |

**Positive questions avg containment:** 0.77  
**Positive questions avg F1:** 0.35  

**Negative tests passed:** 9/9  

### Per-Question Detail

#### Q-G1: Across the agreements, list the **termination/cancellation** rules you can find.

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.06 |
| Containment | 0.93 |
| Precision | 0.36 |
| Recall | 0.93 |
| F1 Score | 0.52 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.94 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5847 |
| Latency P95 (ms) | 67585 |

**Run 1 (67585ms):**

```
- Customer may cancel the purchase contract within 3 business days for a full refund; after this period, the deposit is forfeited [1].
- The PROPERTY MANAGEMENT AGREEMENT may be terminated by either party upon sixty (60) days written notice [2].
- In the event the PROPERTY MANAGEMENT AGREEMENT is terminated, or the property is sold, the Owner must honor all confirmed reservations [5].
- Termination of the PROPERTY MANAGEMENT AGREEMENT does not invalidate any existing rental agreements made by Ag...
```

**Run 2 (5847ms):**

```
- Customer may cancel the purchase contract within 3 business days for a full refund; after this period, the deposit is forfeited [1].
- The PROPERTY MANAGEMENT AGREEMENT may be terminated by either party upon sixty (60) days written notice [2].
- In the event the PROPERTY MANAGEMENT AGREEMENT is terminated or the property is sold, the Owner must honor all confirmed reservations [5].
- Termination of the PROPERTY MANAGEMENT AGREEMENT does not invalidate existing rental agreements made by Agent o...
```

#### Q-G2: Identify which documents reference **jurisdictions / governing law**.

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.04 |
| Containment | 0.94 |
| Precision | 0.18 |
| Recall | 0.94 |
| F1 Score | 0.30 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.52 |
| Citations (Unique) | 3 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4177 |
| Latency P95 (ms) | 4445 |

**Run 1 (4445ms):**

```
- The purchase contract shall be governed by the laws of the State of Florida [1].
- The PROPERTY MANAGEMENT AGREEMENT shall be governed by the laws of the State of Hawaii [2].
- The PROPERTY MANAGEMENT AGREEMENT references an insured financial institution authorized to do business in the State of Hawaii [17].
- The BUILDERS LIMITED WARRANTY states that disputes shall be resolved in accordance with the applicable substantive law of the State of Idaho [3].
- The BUILDERS LIMITED WARRANTY referenc...
```

**Run 2 (4098ms):**

```
- The purchase contract shall be governed by the laws of the State of Florida [1].
- The PROPERTY MANAGEMENT AGREEMENT shall be governed by the laws of the State of Hawaii [2].
- The PROPERTY MANAGEMENT AGREEMENT references an insured financial institution authorized to do business in the State of Hawaii [17].
- The BUILDERS LIMITED WARRANTY states that disputes shall be resolved in accordance with the applicable substantive law of the State of Idaho [3].
- The BUILDERS LIMITED WARRANTY referenc...
```

#### Q-G3: Summarize "who pays what" across the set (fees/charges/taxes).

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.02 |
| Containment | 0.82 |
| Precision | 0.20 |
| Recall | 0.82 |
| F1 Score | 0.32 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.89 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 7530 |
| Latency P95 (ms) | 7626 |

**Run 1 (7530ms):**

```
- Owner pays a non-refundable start-up fee of $250.00 to the Agent upon execution of the Property Management Agreement [3].
- Owner pays a $50.00/month minimum charge for administration and accounting (excluding tax preparation/returns/forms) [7].
- Owner pays a fee/commission of 10% of gross revenues for management services for long-term leases (leases of more than 180 days) [9].
- Owner pays a fee/commission of 25% of gross revenues for management services for short-term and/or vacation rental...
```

**Run 2 (7203ms):**

```
- Owner pays a non-refundable start-up fee of $250.00 to the Agent upon execution of the Property Management Agreement [3].
- Owner pays a $50.00/month minimum charge for administration and accounting (excluding tax preparation/returns/forms) [7].
- Owner pays a fee/commission of 10% of gross revenues for management services for long-term leases (leases of more than 180 days) [9].
- Owner pays a fee/commission of 25% of gross revenues for management services for short-term and/or vacation rental...
```

#### Q-G4: What obligations are explicitly described as **reporting / record-keeping**?

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.02 |
| Containment | 0.88 |
| Precision | 0.13 |
| Recall | 0.88 |
| F1 Score | 0.23 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.53 |
| Citations (Unique) | 3 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 7288 |
| Latency P95 (ms) | 8354 |

**Run 1 (7288ms):**

```
- Provide Owner with a monthly statement of income and expenses for the property [1].
- Complete an initial property inspection and prepare a condition report of the unit [3].
- Conduct a complete inventory of all furniture and furnishings in the rental unit, and produce a condition/inspection report of the premises, appliances, and contents [6].
- Provide the invoice(s) from the media, and pass on the cost to the Owner on the monthly proceeds statements [8].
- Owner to provide Agent with writte...
```

**Run 2 (8354ms):**

```
- Provide Owner with a monthly statement of income and expenses for the property [1]
- Complete an initial property inspection and prepare a condition report of the unit [3]
- Produce a condition/inspection report of the premises, appliances, and contents [6]
- Provide the invoice(s) from the media, and pass on the cost to the Owner on the monthly proceeds statements [8]
- Collect all rents for property and deposit same in a special trust account in an insured financial institution authorized to...
```

#### Q-G5: What remedies / dispute-resolution mechanisms are described?

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.00 |
| Containment | 0.50 |
| Precision | 0.05 |
| Recall | 0.50 |
| F1 Score | 0.08 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.21 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 6938 |
| Latency P95 (ms) | 8869 |

**Run 1 (6938ms):**

```
- Binding arbitration is required for all disputes except those specifically preserved, such as small claims court actions within the jurisdiction limits of the State of Idaho [1], [4], [6].
- Claims for money not exceeding $3,000 may be pursued in the Small Claims Department of the Magistrate Division of the District Courts of the State of Idaho [12].
- Parties may pursue claims of lien or foreclose a lien or mortgage against real or personal property collateral or security, as necessary to pre...
```

**Run 2 (8869ms):**

```
- All disputes (except certain preserved remedies) are subject to binding arbitration. [1]
- Claims for money within the jurisdiction limits of the small claims court of the State of Idaho (not exceeding $3,000) may be pursued in small claims court. [1], [12]
- Parties may pursue claims of lien or foreclose a lien or mortgage against real or personal property collateral or security, as necessary to preserve such remedy or to enforce any arbitration award, or obtain a personal or deficiency award...
```

#### Q-G6: List all **named parties/organizations** across the documents and which document(s) they appear in.

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.07 |
| Containment | 0.73 |
| Precision | 0.32 |
| Recall | 0.73 |
| F1 Score | 0.44 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.83 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5797 |
| Latency P95 (ms) | 6921 |

**Run 1 (5797ms):**

```
- Contoso Ltd. appears in:
  - HOLDING TANK SERVICING CONTRACT [1], [4], [14], [15], [19]
  - purchase contract [3], [5]
  - BUILDERS LIMITED WARRANTY [6], [10]
  - PROPERTY MANAGEMENT AGREEMENT [7], [8], [9]
- Fabrikam Inc. appears in:
  - HOLDING TANK SERVICING CONTRACT [1], [4]
  - purchase contract [2], [3], [5]
  - BUILDERS LIMITED WARRANTY [6], [10], [13]
  - PROPERTY MANAGEMENT AGREEMENT [8], [9]
- Contoso Lifts LLC appears in:
  - purchase contract [2]
  - contoso lifts invoice [12], [17...
```

**Run 2 (4985ms):**

```
- Contoso Ltd. appears in:
  - HOLDING TANK SERVICING CONTRACT [1], [4], [14], [15], [19]
  - purchase contract [3], [5]
  - BUILDERS LIMITED WARRANTY [6], [10]
  - PROPERTY MANAGEMENT AGREEMENT [7], [8], [9]

- Fabrikam Inc. appears in:
  - HOLDING TANK SERVICING CONTRACT [1], [4]
  - purchase contract [2], [3], [5]
  - BUILDERS LIMITED WARRANTY [6], [10], [13]
  - PROPERTY MANAGEMENT AGREEMENT [8], [9]

- Contoso Lifts LLC appears in:
  - purchase contract [2]
  - contoso lifts invoice [12], [...
```

#### Q-G7: Summarize all explicit **notice / delivery** mechanisms (written notice, certified mail, phone, filings) mentioned.

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.09 |
| Containment | 0.91 |
| Precision | 0.28 |
| Recall | 0.91 |
| F1 Score | 0.42 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.27 |
| Citations (Unique) | 2 |
| Evidence Path (Unique) | 2 |
| Latency P50 (ms) | 4647 |
| Latency P95 (ms) | 4931 |

**Run 1 (4647ms):**

```
- Written notice of defects must be sent by letter via certified mail return receipt requested to the Builder's office address. [1]
- Emergency notifications may be made by telephone to the Builder; only emergency reports will be taken by phone. [4]
- Claims must be made in writing as provided in the warranty to be covered. [8], [15]
- The Buyer/Owner must inform the Builder in writing of times they will be at home for scheduling service calls. [9]
- No modifications to the Agreement are effecti...
```

**Run 2 (4572ms):**

```
- Buyer/Owner must write a letter describing the defect and send it by certified mail return receipt requested to the Builder at the Builder's office address for warranty claims. [1]
- Emergency reports may be made by telephone to the Builder; only emergency reports will be taken by phone. [4]
- Buyer/Owner must notify the Builder in writing of times they will be at home for scheduling service calls. [9]
- Any claims not made in writing within the specified warranty period are not covered. [8], ...
```

#### Q-G8: Summarize all explicit **insurance / indemnity / hold harmless** clauses.

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.07 |
| Containment | 0.82 |
| Precision | 0.31 |
| Recall | 0.82 |
| F1 Score | 0.44 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.98 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 5763 |
| Latency P95 (ms) | 34875 |

**Run 1 (34875ms):**

```
- Owner agrees that Agent shall not be liable for any claim for loss or injury to any person or property located on the property, except for loss or injury caused by Agent's gross negligence or willful misconduct, and Owner shall hold Agent harmless and indemnify Agent for any such claim or liability [1].
- Owner must provide liability insurance coverage for the property with minimum limits of $300,000 for bodily injury and $25,000 for property damage to others; Agent shall be named as additiona...
```

**Run 2 (5763ms):**

```
- Owner agrees that Agent shall not be liable for any claim for loss or injury to any person or property located on the property subject to this agreement, except for loss or injury caused by Agent's gross negligence or wilful misconduct, and Owner shall hold Agent harmless and indemnify Agent for any such claim or liability [1].
- Owner must provide liability insurance coverage for the property with minimum limits of $300,000 for bodily injury and $25,000 for property damage to others; Agent sh...
```

#### Q-G9: Identify all explicit **non-refundable / forfeiture** terms across the documents.

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.44 |
| Containment | 0.61 |
| Precision | 0.37 |
| Recall | 0.61 |
| F1 Score | 0.46 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.80 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 3645 |
| Latency P95 (ms) | 3653 |

**Run 1 (3645ms):**

```
- Upon the execution of this Agreement, the Owner shall pay two hundred fifty dollars ($250.00) to the Agent as a non-refundable start-up fee. [1]
- Afterward, deposit is forfeited. [2]
```

**Run 2 (3401ms):**

```
- Upon the execution of the PROPERTY MANAGEMENT AGREEMENT, the Owner shall pay two hundred fifty dollars ($250.00) to the Agent as a non-refundable start-up fee. [1]
- In the purchase contract, after the initial period, the deposit is forfeited. [2]
```

#### Q-G10: Summarize each document's main purpose in one sentence.

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.02 |
| Containment | 0.57 |
| Precision | 0.17 |
| Recall | 0.57 |
| F1 Score | 0.27 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.33 |
| Min Similarity | 0.80 |
| Citations (Unique) | 3 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 4608 |
| Latency P95 (ms) | 34866 |

**Run 1 (4454ms):**

```
- The main purpose of the PROPERTY MANAGEMENT AGREEMENT is to appoint an agent to exclusively rent, lease, operate, and manage the owner's property, detailing the agent's responsibilities and obligations for property management and reporting [10], [4], [5], [7], [17], [1], [25].

- The main purpose of the BUILDERS LIMITED WARRANTY is to provide the first purchaser of a home with a one-year warranty against defects in materials or workmanship for specified structural and system components, and to...
```

**Run 2 (34866ms):**

```
- The main purpose of the PROPERTY MANAGEMENT AGREEMENT is to appoint an agent to exclusively rent, lease, operate, and manage the owner's property, detailing the agent's responsibilities and obligations in managing the property on behalf of the owner [10], [25].
- The main purpose of the BUILDERS LIMITED WARRANTY is to provide the buyer/owner with a one-year warranty against defects in materials or workmanship for specified structural and system components of the home, and to establish binding ...
```

#### Q-N1: What is the invoice's **bank routing number** for payment?

**Runs:** 3

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
| Latency P50 (ms) | 3099 |
| Latency P95 (ms) | 3233 |

**Run 1 (3074ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (3233ms):**

```
- The requested information was not found in the available documents.
```

#### Q-N2: What is the invoice’s **IBAN / SWIFT (BIC)** for international payments?

**Runs:** 3

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
| Latency P50 (ms) | 3079 |
| Latency P95 (ms) | 33515 |

**Run 1 (3079ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (33515ms):**

```
- The requested information was not found in the available documents.
```

#### Q-N3: What is the vendor's **VAT / Tax ID number** on the invoice?

**Runs:** 3

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
| Evidence Path (Unique) | 2 |
| Latency P50 (ms) | 3076 |
| Latency P95 (ms) | 3121 |

**Run 1 (2980ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (3076ms):**

```
- The requested information was not found in the available documents.
```

#### Q-N5: What is the invoice’s **bank account number** for ACH/wire payments?

**Runs:** 3

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
| Latency P50 (ms) | 2853 |
| Latency P95 (ms) | 33557 |

**Run 1 (33557ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (2853ms):**

```
- The requested information was not found in the available documents.
```

#### Q-N6: Which documents are governed by the laws of **California**?

**Runs:** 3

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
| Latency P50 (ms) | 3026 |
| Latency P95 (ms) | 34019 |

**Run 1 (2983ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (3026ms):**

```
- The requested information was not found in the available documents.
```

#### Q-N7: What is the property management Agent's **license number**?

**Runs:** 3

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
| Latency P50 (ms) | 2727 |
| Latency P95 (ms) | 2806 |

**Run 1 (2727ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (2672ms):**

```
- The requested information was not found in the available documents.
```

#### Q-N8: What is the purchase contract’s required **wire transfer / ACH instructions**?

**Runs:** 3

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | PASS |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 0.67 |
| Min Similarity | 0.99 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 2 |
| Latency P50 (ms) | 2844 |
| Latency P95 (ms) | 33599 |

**Run 1 (2844ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (2732ms):**

```
The requested information was not found in the available documents.
```

#### Q-N9: What is the exact clause about **mold damage** coverage in the warranty?

**Runs:** 3

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
| Latency P50 (ms) | 2932 |
| Latency P95 (ms) | 2944 |

**Run 1 (2944ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (2932ms):**

```
- The requested information was not found in the available documents.
```

#### Q-N10: What is the invoice **shipping method** (value in "SHIPPED VIA")?

**Runs:** 3

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
| Latency P50 (ms) | 2801 |
| Latency P95 (ms) | 33606 |

**Run 1 (2801ms):**

```
- The requested information was not found in the available documents.
```

**Run 2 (33606ms):**

```
- The requested information was not found in the available documents.
```

---

