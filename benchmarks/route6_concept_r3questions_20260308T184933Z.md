# Route 7 (HippoRAG 2) Benchmark

**Timestamp:** 20260308T184933Z

**API Base URL:** `http://localhost:8000`

**Group ID:** `test-5pdfs-v2-fix2`

**Force Route:** `concept_search`

**Architecture:** True HippoRAG 2 with passage-node PPR, query-to-triple linking, and recognition memory filtering.

---

## Scenario: route6_concept_r3questions_summary

**Response Type:** `summary`

### Summary Table

| QID | Containment | F1 | Neg Pass | Exact Rate | Min Sim | P50 ms | P95 ms |
|-----|-------------|-----|----------|------------|---------|--------|--------|
| Q-G1 | 0.98 | 0.41 | - | 1.00 | 1.00 | 73841 | 73841 |
| Q-G2 | 1.00 | 0.19 | - | 1.00 | 1.00 | 14845 | 14845 |
| Q-G3 | 0.89 | 0.26 | - | 1.00 | 1.00 | 26501 | 26501 |
| Q-G4 | 0.88 | 0.22 | - | 1.00 | 1.00 | 25624 | 25624 |
| Q-G5 | 0.70 | 0.09 | - | 1.00 | 1.00 | 22955 | 22955 |
| Q-G6 | 0.95 | 0.32 | - | 1.00 | 1.00 | 12648 | 12648 |
| Q-G7 | 0.91 | 0.27 | - | 1.00 | 1.00 | 29266 | 29266 |
| Q-G8 | 0.77 | 0.20 | - | 1.00 | 1.00 | 15168 | 15168 |
| Q-G9 | 0.94 | 0.27 | - | 1.00 | 1.00 | 14068 | 14068 |
| Q-G10 | 0.77 | 0.38 | - | 1.00 | 1.00 | 20953 | 20953 |
| Q-N1 | - | - | PASS | 1.00 | 1.00 | 18690 | 18690 |
| Q-N2 | - | - | PASS | 1.00 | 1.00 | 19098 | 19098 |
| Q-N3 | - | - | PASS | 1.00 | 1.00 | 21699 | 21699 |
| Q-N5 | - | - | PASS | 1.00 | 1.00 | 19708 | 19708 |
| Q-N6 | - | - | FAIL | 1.00 | 1.00 | 21538 | 21538 |
| Q-N7 | - | - | PASS | 1.00 | 1.00 | 19979 | 19979 |
| Q-N8 | - | - | PASS | 1.00 | 1.00 | 27065 | 27065 |
| Q-N9 | - | - | PASS | 1.00 | 1.00 | 13502 | 13502 |
| Q-N10 | - | - | PASS | 1.00 | 1.00 | 20418 | 20418 |

**Positive questions avg containment:** 0.88  
**Positive questions avg F1:** 0.26  

**Negative tests passed:** 8/9  

### Per-Question Detail

#### Q-G1: Across the agreements, list the **termination/cancellation** rules you can find.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.04 |
| Containment | 0.98 |
| Precision | 0.26 |
| Recall | 0.98 |
| F1 Score | 0.41 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 73841 |
| Latency P95 (ms) | 73841 |

**Run 1 (73841ms):**

```
**Termination/Cancellation Rules Across the Agreements**

---

### PROPERTY MANAGEMENT AGREEMENT

- **Term and Renewal**: The agreement is for an initial period of twelve months beginning on 2010-06-15 and is automatically renewed for successive one-year terms thereafter.
  - [PROPERTY MANAGEMENT AGREEMENT > PROPERTY MANAGEMENT AGREEMENT (Short Term and/or Vacation/Holiday Rentals)]

- **Termination by Either Party**: Either party may terminate the agreement upon sixty (60) days written notice.
...
```

#### Q-G2: Identify which documents reference **jurisdictions / governing law**.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.04 |
| Containment | 1.00 |
| Precision | 0.11 |
| Recall | 1.00 |
| F1 Score | 0.19 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 14845 |
| Latency P95 (ms) | 14845 |

**Run 1 (14845ms):**

```
**References to Jurisdictions / Governing Law by Document**

---

### PURCHASE CONTRACT

- **Section Referenced:** [purchase_contract > section_0 > PURCHASE CONTRACT > 7. Applicable Law]
- **Governing Law Clause:** "This contract shall be governed by the laws of the State of Florida."
- **Additional Details:** The contract also specifies that neither party may assign the contract without the other's written consent.

---

### PROPERTY MANAGEMENT AGREEMENT (Short Term and/or Vacation/Holiday Rent...
```

#### Q-G3: Summarize "who pays what" across the set (fees/charges/taxes).

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.04 |
| Containment | 0.89 |
| Precision | 0.15 |
| Recall | 0.89 |
| F1 Score | 0.26 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 26501 |
| Latency P95 (ms) | 26501 |

**Run 1 (26501ms):**

```
Below is a summary of "who pays what" (fees, charges, taxes) across the set, organized by contractual relationship and role, with specific details and terminology preserved.

---

**1. Customer (Fabrikam Inc.) – Lift Purchase and Installation (Contoso Lifts LLC)**

- **Total Contract Price:** Customer pays $29,900.00 for the lift purchase and installation, as specified in [purchase_contract > section_0 > PURCHASE CONTRACT > 2. Payment Terms] and [contoso_lifts_invoice > section_0 > INVOICE].
   ...
```

#### Q-G4: What obligations are explicitly described as **reporting / record-keeping**?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.03 |
| Containment | 0.88 |
| Precision | 0.13 |
| Recall | 0.88 |
| F1 Score | 0.22 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 25624 |
| Latency P95 (ms) | 25624 |

**Run 1 (25624ms):**

```
Below is a complete list of obligations explicitly described as **reporting / record-keeping** in the available documents, organized by thematic area:

---

### 1. Owner-Agent Relationships in Property Rental Agreements

**A. Monthly Statements and Financial Records**
- The Agent is required to provide the Owner with a **monthly statement of income and expenses for the property**. [(PROPERTY MANAGEMENT AGREEMENT > PROPERTY MANAGEMENT AGREEMENT (Short Term and/or Vacation/Holiday Rentals))]

**B....
```

#### Q-G5: What remedies / dispute-resolution mechanisms are described?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.00 |
| Containment | 0.70 |
| Precision | 0.05 |
| Recall | 0.70 |
| F1 Score | 0.09 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 22955 |
| Latency P95 (ms) | 22955 |

**Run 1 (22955ms):**

```
The remedies and dispute-resolution mechanisms described in the available documents are as follows:

---

**1. Binding Arbitration (Primary Dispute Resolution Mechanism)**
- **Scope:** All disputes (as defined) that cannot be litigated in the Small Claims Court of the State of Idaho are subject to binding arbitration. This includes any action, dispute, claim, or controversy of any kind, whether founded in contract, tort, statutory or common law, equity, or otherwise, arising out of or in connect...
```

#### Q-G6: List all **named parties/organizations** across the documents and which document(s) they appear in.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.03 |
| Containment | 0.95 |
| Precision | 0.19 |
| Recall | 0.95 |
| F1 Score | 0.32 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 12648 |
| Latency P95 (ms) | 12648 |

**Run 1 (12648ms):**

```
Below is a complete list of all **named parties/organizations** found across the documents, along with the specific document(s) in which each appears. Entities are grouped by organizational relationship for clarity.

---

### Contoso Entities

- **Contoso Lifts LLC**
  - Appears in:  
    - [contoso_lifts_invoice]  
    - [purchase_contract]  
  - (Referenced as the contractor and payee in invoices and contracts.)

- **Contoso Ltd.**
  - Appears in:  
    - [PROPERTY MANAGEMENT AGREEMENT]  
    ...
```

#### Q-G7: Summarize all explicit **notice / delivery** mechanisms (written notice, certified mail, phone, filings) mentioned.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.03 |
| Containment | 0.91 |
| Precision | 0.16 |
| Recall | 0.91 |
| F1 Score | 0.27 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 29266 |
| Latency P95 (ms) | 29266 |

**Run 1 (29266ms):**

```
Below is a summary of all explicit **notice / delivery** mechanisms (written notice, certified mail, phone, filings) mentioned across the provided documents, organized by type and context:

---

### 1. Written Notice

- **Defect Notification (Warranty Claims):**
  - The Buyer/Owner must write a letter describing the defect to the Builder and send it by certified mail return receipt requested to the Builder’s office address. ([BUILDERS LIMITED WARRANTY > BUILDERS LIMITED WARRANTY WITH ARBITRATION...
```

#### Q-G8: Summarize all explicit **insurance / indemnity / hold harmless** clauses.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.05 |
| Containment | 0.77 |
| Precision | 0.12 |
| Recall | 0.77 |
| F1 Score | 0.20 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 15168 |
| Latency P95 (ms) | 15168 |

**Run 1 (15168ms):**

```
Below is a complete summary of all explicit **insurance, indemnity, and hold harmless** clauses found in the available documents, organized by thematic context and preserving all specific details:

---

### 1. Owner’s Liability Insurance Requirements

- **PROPERTY MANAGEMENT AGREEMENT (Short Term and/or Vacation/Holiday Rentals):**
  - The Owner is required to provide Liability Insurance coverage for the property with minimum limits of **$300,000 for bodily injury** and **$25,000 for property da...
```

#### Q-G9: Identify all explicit **non-refundable / forfeiture** terms across the documents.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.06 |
| Containment | 0.94 |
| Precision | 0.16 |
| Recall | 0.94 |
| F1 Score | 0.27 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 14068 |
| Latency P95 (ms) | 14068 |

**Run 1 (14068ms):**

```
**Explicit Non-Refundable / Forfeiture Terms Across All Documents**

---

### 1. Property Management Agreements

- **Non-Refundable Start-Up Fee**
  - [PROPERTY MANAGEMENT AGREEMENT > PROPERTY MANAGEMENT AGREEMENT (Short Term and/or Vacation/Holiday Rentals) > PROPERTY MANAGEMENT AGREEMENT:]
    - "Upon the execution of this Agreement, the Owner shall pay two hundred fifty dollars ($250.00) to the Agent as a non-refundable start-up fee."
    - The fee is used for initial administrative expenses,...
```

#### Q-G10: Summarize each document's main purpose in one sentence.

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match | No |
| Fuzzy Score | 0.06 |
| Containment | 0.77 |
| Precision | 0.25 |
| Recall | 0.77 |
| F1 Score | 0.38 |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 20953 |
| Latency P95 (ms) | 20953 |

**Run 1 (20953ms):**

```
**Summary of Each Document’s Main Purpose**

**PROPERTY MANAGEMENT AGREEMENT**  
The PROPERTY MANAGEMENT AGREEMENT sets out the terms and responsibilities under which an Agent manages, rents, and maintains an Owner’s property, including financial arrangements, property inspections, reporting, and the handling of reservations and administrative fees for short-term or vacation rentals.

**HOLDING TANK SERVICING CONTRACT**  
The HOLDING TANK SERVICING CONTRACT defines the obligations of the propert...
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
| Latency P50 (ms) | 18690 |
| Latency P95 (ms) | 18690 |

**Run 1 (18690ms):**

```
**Bank Routing Number for Payment**

**Summary of Findings**

- The invoice and related contract documents for Contoso Lifts LLC do not provide a bank routing number for payment.

**Detailed Evidence**

- Thematic context confirms that the invoice states: "Make all checks payable to Contoso Lifts LLC" and provides addresses and phone numbers, but does not list a bank routing number for payment. It also explicitly states that no bank routing number is provided anywhere in the invoice or related c...
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
| Latency P50 (ms) | 19098 |
| Latency P95 (ms) | 19098 |

**Run 1 (19098ms):**

```
**Framing from Thematic Context**

The thematic context indicates that the invoice does not list an IBAN or SWIFT (BIC) code for international payments. This is a direct summary of the available information regarding international payment details.

**Findings from Document Evidence**

A review of the document evidence, including all sections of the invoice ([contoso_lifts_invoice > section_0 > INVOICE]) and the purchase contract, shows no mention of an IBAN or SWIFT (BIC) code. The payment instr...
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
| Latency P50 (ms) | 21699 |
| Latency P95 (ms) | 21699 |

**Run 1 (21699ms):**

```
**Vendor VAT / Tax ID Number on the Invoice**

**Thematic Context**
- The community summary explicitly states: "The invoice from Contoso Lifts LLC does not list a VAT or Tax ID number."

**Document Evidence**
- [contoso_lifts_invoice > section_0 > INVOICE]: The invoice includes details such as INVOICE # 1256003, CUSTOMER ID #: 4905201, dates, payment instructions, and company contact information, but there is no mention of a VAT or Tax ID number.
- [contoso_lifts_invoice > [Letterhead]]: The com...
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
| Latency P50 (ms) | 19708 |
| Latency P95 (ms) | 19708 |

**Run 1 (19708ms):**

```
**Bank Account Number for ACH/Wire Payments**

**Thematic Context: Payment Instructions**
The invoice emphasizes that "all checks [should be] payable to Contoso Lifts LLC" and provides an online payment portal (https://ww.contosolifts.com/portal/pay) for electronic payments. However, it is specifically noted that the invoice does not list a bank account number for ACH or wire payments.

**Document Evidence: Payment Details**
- [contoso_lifts_invoice > section_0 > INVOICE] repeatedly instructs pa...
```

#### Q-N6: Which documents are governed by the laws of **California**?

**Runs:** 1

**Accuracy Metrics:**

| Metric | Value |
|--------|-------|
| Negative Test | FAIL |

**Repeatability Metrics:**

| Metric | Value |
|--------|-------|
| Exact Match Rate | 1.00 |
| Min Similarity | 1.00 |
| Citations (Unique) | 1 |
| Evidence Path (Unique) | 1 |
| Latency P50 (ms) | 21538 |
| Latency P95 (ms) | 21538 |

**Run 1 (21538ms):**

```
Based on the available evidence, NO documents are governed by the laws of California.

**Findings by Document:**

- **BUILDERS LIMITED WARRANTY:** Disputes are resolved in accordance with the substantive law of the State of Idaho. (See: [BUILDERS LIMITED WARRANTY > BUILDERS LIMITED WARRANTY WITH ARBITRATION > 2. Term.])
- **PROPERTY MANAGEMENT AGREEMENT:** This agreement is governed by the laws of the State of Hawaii. (See: [PROPERTY MANAGEMENT AGREEMENT > PROPERTY MANAGEMENT AGREEMENT (Short Te...
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
| Latency P50 (ms) | 19979 |
| Latency P95 (ms) | 19979 |

**Run 1 (19979ms):**

```
**Property Management Agent's License Number**

**Summary of Findings**

- The thematic context explicitly states that the PROPERTY MANAGEMENT AGREEMENT and related documents do not list a license number for the Agent (Walt Flood Realty).
- Review of the document evidence, including all relevant sections and signature blocks, confirms that no license number for the Agent is provided.
- The Agent is identified as "Walt Flood Realty, a Hawaii sole proprietorship," but no license number is mentione...
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
| Latency P50 (ms) | 27065 |
| Latency P95 (ms) | 27065 |

**Run 1 (27065ms):**

```
**Wire Transfer / ACH Instructions in the Purchase Contract**

**1. Explicit Payment Methods Required by the Contract and Invoice**

The purchase contract and associated invoice do **not** provide any explicit wire transfer or ACH instructions. Instead, the required payment methods are as follows:

- **Check Payment:** The contract and invoice specify that all checks should be made payable to Contoso Lifts LLC.  
  - [contoso_lifts_invoice > section_0 > INVOICE]: "Make all checks payable to Cont...
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
| Latency P50 (ms) | 13502 |
| Latency P95 (ms) | 13502 |

**Run 1 (13502ms):**

```
The requested information was not found in the available documents.
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
| Latency P50 (ms) | 20418 |
| Latency P95 (ms) | 20418 |

**Run 1 (20418ms):**

```
**Framing by Thematic Context: SHIPPED VIA**

The thematic context identifies "SHIPPED VIA" as a relevant field for the invoice shipping method, but notes its value as "N/A" in the context of Contoso-Fabrikam contractual and property relationships.

---

**Document Evidence: Shipping Method ("SHIPPED VIA")**

- [contoso_lifts_invoice > section_0 > INVOICE]: Multiple passages provide invoice details (invoice number, customer, ship to, payment instructions, item descriptions, totals), but none men...
```

---

