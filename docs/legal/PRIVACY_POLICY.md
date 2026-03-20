# Privacy Policy

**Effective Date:** March 28, 2026
**Last Updated:** 2026-03-20

---

## 1. Introduction

This Privacy Policy describes how **BangDesign Co. Ltd.** ("Company", "we", "us", or "our") collects, uses, stores, and protects your personal data when you use **Evidoc** ("Service").

We are committed to complying with the **Thailand Personal Data Protection Act B.E. 2562 (2019)** ("PDPA"), the **EU General Data Protection Regulation** ("GDPR") where applicable, and other relevant data protection laws.

By using the Service, you acknowledge that you have read and understood this Privacy Policy. Where we rely on consent as our legal basis, we will obtain your explicit consent before processing.

---

## 2. Data Controller

**BangDesign Co. Ltd.**
Email: support@hulkdesign.com

For data protection inquiries, contact our Data Protection Officer at: support@hulkdesign.com (Subject: "Data Protection Inquiry").

---

## 3. Personal Data We Collect

### 3.1 Account Data (collected at registration)

| Data | Source | Purpose |
|------|--------|---------|
| Name / display name | Azure AD / Entra ID (B2B) or Azure AD B2C (B2C) | Account identification |
| Email address | Identity provider | Communication, billing, account recovery |
| Azure AD Object ID (oid) | Identity provider | Unique user identifier |
| Tenant ID | Identity provider (B2B) | Organization identification |
| Group memberships | Azure AD (B2B) | Role-based access control, data isolation |
| App roles (Admin/User) | Azure AD | Authorization |

### 3.2 Payment Data (paid plans only)

| Data | Source | Purpose |
|------|--------|---------|
| Stripe Customer ID | Stripe | Subscription management |
| Stripe Subscription ID | Stripe | Billing cycle tracking |
| Plan tier and status | Stripe webhooks | Feature access, quota enforcement |
| Billing period dates | Stripe | Credit cycle management |

We do **not** store your credit card number, CVV, or full payment details. All payment processing is handled by **Stripe**, which is PCI DSS Level 1 compliant. See [Stripe's Privacy Policy](https://stripe.com/privacy).

### 3.3 Documents You Upload

| Data | Storage | Purpose |
|------|---------|---------|
| Original files (PDF, Word, Excel, images, etc.) | Azure Blob Storage (encrypted at rest) | Source documents for processing |
| Extracted text, tables, and layout data | Neo4j (Knowledge Graph) | Question answering, citation retrieval |
| Entity and relationship data | Neo4j | Cross-document reasoning |
| Semantic embeddings (vector representations) | Neo4j + Azure Cognitive Search | Similarity search |
| Word-level bounding box coordinates | Neo4j | Click-to-verify PDF highlighting |

**Important:** We process your documents solely to provide the Service. We do **not** use your documents to train AI models.

### 3.4 Usage Data (generated during use)

| Data | Storage | Retention | Purpose |
|------|---------|-----------|---------|
| Queries submitted | Azure Cosmos DB | 90 days | Chat history, service improvement |
| AI-generated answers | Azure Cosmos DB | 90 days | Chat history continuity |
| Operation type, model used, token counts | Azure Cosmos DB | 90 days | Usage metering, credit deduction |
| Credits consumed per operation | Azure Cosmos DB | 90 days | Billing accuracy |
| Route selected (algorithm path) | Azure Cosmos DB | 90 days | Performance optimization |
| Detected language, translation events | Azure Cosmos DB | 90 days | Multilingual service delivery |
| Pages processed (OCR) | Azure Cosmos DB | 90 days | Document Intelligence metering |
| Query timestamps | Azure Cosmos DB | 90 days | Rate limit enforcement |

### 3.5 Analytics Data (opt-in only)

**PostHog (product analytics)** — Collected only when enabled via configuration:
- User ID (pseudonymized), tenant ID
- Events: query sent, query completed, citation clicked, file uploaded, dashboard viewed, plan upgrade clicked, rate limit hit
- Query latency, credits consumed, route used
- **Not collected:** query text, document content, AI answers

**Sentry (error tracking)** — Collected only when enabled via configuration:
- Error stack traces and metadata
- 10% sampling of transactions
- **PII stripping:** Console breadcrumb messages are removed before transmission; no query text is sent to Sentry

### 3.6 Technical Data (collected automatically)

- IP address (in server logs, not persisted beyond standard log rotation)
- Browser type and version (via standard HTTP headers)
- Authentication tokens (JWT, processed in memory, not persisted)

---

## 4. Legal Basis for Processing

Under the PDPA and GDPR (where applicable), we process your data on the following legal bases:

| Processing Activity | Legal Basis (PDPA) | Legal Basis (GDPR) |
|---------------------|--------------------|--------------------|
| Account creation and authentication | Contract performance | Contract (Art. 6(1)(b)) |
| Document processing and Q&A | Contract performance | Contract (Art. 6(1)(b)) |
| Usage metering and billing | Contract performance | Contract (Art. 6(1)(b)) |
| Rate limit enforcement | Legitimate interest | Legitimate interest (Art. 6(1)(f)) |
| Product analytics (PostHog) | Consent | Consent (Art. 6(1)(a)) |
| Error tracking (Sentry) | Legitimate interest | Legitimate interest (Art. 6(1)(f)) |
| Security and fraud prevention | Legitimate interest | Legitimate interest (Art. 6(1)(f)) |
| Legal compliance | Legal obligation | Legal obligation (Art. 6(1)(c)) |

---

## 5. How We Use Your Data

We use your personal data to:

1. **Provide the Service** — process your documents, answer your queries, and display citations
2. **Manage your account** — authentication, authorization, and plan management
3. **Process payments** — subscription billing via Stripe
4. **Enforce limits** — daily/monthly query quotas, storage limits, and credit consumption
5. **Improve the Service** — aggregate, anonymized usage analytics (never individual document content)
6. **Ensure security** — detect and prevent unauthorized access, abuse, and fraud
7. **Communicate with you** — service updates, billing notifications, and support responses
8. **Comply with law** — respond to lawful requests from authorities

We do **not**:
- Sell your personal data to third parties
- Use your documents or queries to train AI models
- Share your data with advertisers
- Create advertising profiles from your usage

---

## 6. Data Sharing and Third-Party Processors

We share your data only with the following categories of processors, solely to provide the Service:

### 6.1 Infrastructure and AI Processors

| Processor | Location | Data Shared | Purpose |
|-----------|----------|-------------|---------|
| **Microsoft Azure** (hosting, OCR, auth, storage, translation, speech) | As configured (typically Southeast Asia / East Asia regions) | Documents, account data, queries | Core infrastructure |
| **Azure OpenAI Service** | Azure region | Query text, document excerpts (as context) | AI answer generation |
| **Voyage AI** | United States | Document text chunks (for embedding) | Semantic search and reranking |
| **Neo4j Aura** | As configured | Extracted entities, text, embeddings | Knowledge Graph storage |

### 6.2 Payment Processor

| Processor | Location | Data Shared | Purpose |
|-----------|----------|-------------|---------|
| **Stripe** | United States / Global | Email, plan tier, payment method (handled by Stripe) | Subscription billing |

### 6.3 Analytics (opt-in only)

| Processor | Location | Data Shared | Purpose |
|-----------|----------|-------------|---------|
| **PostHog** | EU / US (configurable) | Pseudonymized usage events | Product analytics |
| **Sentry** | United States | Error metadata (PII stripped) | Error tracking |

### 6.4 Other Disclosures

We may disclose your data if required by:
- A valid court order or legal process
- Applicable law or regulation
- Protection of our rights, property, or safety, or that of our users

---

## 7. International Data Transfers

Your data may be transferred to and processed in countries outside of Thailand, including the United States and EU/EEA member states. When we transfer data internationally, we ensure appropriate safeguards are in place, including:

- **Standard Contractual Clauses (SCCs)** where required
- **Adequacy decisions** where applicable
- **Processor agreements** with all third-party services

Under the PDPA, we ensure that destination countries have adequate data protection standards or that appropriate safeguards are implemented as required by the Personal Data Protection Committee.

---

## 8. Data Retention

| Data Category | Retention Period | Deletion Method |
|---------------|-----------------|-----------------|
| **Account data** | Duration of account + 30 days | Automated upon account termination |
| **Uploaded documents** | Until user deletes or account terminates + 30 days | User-initiated or automated |
| **Knowledge Graph data** | Until source document is deleted | Cascade deletion with document |
| **Chat history** | 90 days (automatic TTL) | Automatic expiry in Cosmos DB |
| **Usage records** | 90 days (automatic TTL) | Automatic expiry in Cosmos DB |
| **Subscription records** | Duration of subscription + 7 years (tax/legal) | Manual deletion after retention period |
| **Redis quota data** | 48 hours (daily) / 35 days (monthly) | Automatic TTL expiry |
| **Payment data** | Managed by Stripe per their retention policy | Via Stripe |
| **Analytics data** | Per PostHog/Sentry retention policies | Via respective providers |

After retention periods expire, data is permanently deleted and cannot be recovered.

---

## 9. Data Security

We implement the following security measures to protect your data:

- **Encryption at rest:** All documents in Azure Blob Storage are encrypted using Azure-managed keys (AES-256). Neo4j Aura uses encryption at rest.
- **Encryption in transit:** All data transmitted between your browser, our API, and third-party services uses TLS 1.2+.
- **Authentication:** Azure AD / Entra ID with JWT token validation via JWKS endpoints. Tokens are validated on every request.
- **Tenant isolation:** Documents and Knowledge Graph data are isolated by group ID. Multi-tenant queries never cross tenant boundaries.
- **Secret management:** API keys and credentials are stored in Azure Key Vault, not in application code.
- **Access control:** Role-based access (Admin/User) enforced at the API layer.
- **Rate limiting:** Redis-based atomic quota enforcement prevents abuse.
- **Error handling:** Sentry integration strips PII from error reports before transmission.

---

## 10. Your Rights

### 10.1 Under the PDPA (Thailand)

As a data subject under the PDPA, you have the right to:

| Right | Description |
|-------|-------------|
| **Access** | Request a copy of your personal data we hold |
| **Correction** | Request correction of inaccurate or incomplete data |
| **Deletion** | Request deletion of your data (subject to legal retention requirements) |
| **Restriction** | Request restriction of processing in certain circumstances |
| **Objection** | Object to processing based on legitimate interest |
| **Portability** | Receive your data in a structured, machine-readable format |
| **Withdraw consent** | Withdraw consent at any time (without affecting prior lawful processing) |
| **Complaint** | Lodge a complaint with the Personal Data Protection Committee (PDPC) |

### 10.2 Under the GDPR (EU/EEA users)

If you are located in the EU/EEA, you additionally have the right to:
- Lodge a complaint with your local Data Protection Authority (DPA)
- Object to automated decision-making (note: the Service does not make solely automated decisions with legal effects)

### 10.3 Exercising Your Rights

To exercise any of these rights, contact us at:

**Email:** support@hulkdesign.com
**Subject:** "Data Subject Request — [Your Right]"

We will respond within **30 days** of receiving your request. We may ask for identity verification before processing your request.

### 10.4 Self-Service Data Management

You can directly manage your data through the Service:
- **Download documents:** Via the file management interface
- **Delete documents:** Removes the file and all associated Knowledge Graph data
- **Delete chat history:** Chat sessions auto-expire after 90 days
- **Delete account:** Contact support@hulkdesign.com

---

## 11. Children's Privacy

The Service is not directed to individuals under the age of 18 (or the age of majority in the applicable jurisdiction). We do not knowingly collect personal data from children. If we learn that we have collected data from a child, we will delete it promptly. If you believe a child has provided us with personal data, please contact us at support@hulkdesign.com.

---

## 12. Cookies and Local Storage

For details on cookies, local storage, and similar technologies used by the Service, please refer to our [Cookie Policy](./COOKIE_POLICY.md).

In summary:
- We use **session storage** for authentication tokens
- We use **local storage** for UI preferences and analytics (PostHog, when opted-in)
- We do **not** use third-party advertising cookies

---

## 13. Changes to This Privacy Policy

We may update this Privacy Policy from time to time. When we make material changes, we will:
- Update the "Last Updated" date at the top of this page
- Notify you via email or an in-app notification
- Where required by law, obtain your renewed consent

Your continued use of the Service after changes take effect constitutes acceptance of the revised Privacy Policy.

---

## 14. Governing Law

This Privacy Policy is governed by the laws of the **Kingdom of Thailand**, including the Personal Data Protection Act B.E. 2562 (2019). For users in the EU/EEA, the GDPR applies in addition to the PDPA.

---

## 15. Contact Us

For any questions, concerns, or requests related to this Privacy Policy or your personal data:

**BangDesign Co. Ltd.**
**Data Protection Officer**
Email: support@hulkdesign.com
Subject: "Privacy Inquiry"

For complaints regarding data protection, you may also contact:
- **Thailand:** The Personal Data Protection Committee (PDPC) — [www.pdpc.or.th](https://www.pdpc.or.th)
- **EU/EEA:** Your local Data Protection Authority

---

*This Privacy Policy was last updated on 2026-03-20.*
