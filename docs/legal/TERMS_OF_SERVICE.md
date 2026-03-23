# Terms of Service

**Effective Date:** March 28, 2026
**Last Updated:** 2026-03-20

---

## 1. Introduction

Welcome to **Evidoc** ("Service"), a document intelligence platform operated by **BangDesign Co. Ltd.** ("Company", "we", "us", or "our").

By accessing or using Evidoc at [https://app.evidoc.hulkdesign.com](https://app.evidoc.hulkdesign.com) or any associated applications, you ("User", "you", or "your") agree to be bound by these Terms of Service ("Terms"). If you do not agree, do not use the Service.

These Terms constitute a legally binding agreement between you and BangDesign Co. Ltd.. For enterprise or business accounts, "you" refers to the organization on whose behalf the account is created, and the individual accepting these Terms represents that they have authority to bind that organization.

---

## 2. Description of Service

Evidoc is an AI-powered document intelligence platform that enables users to:

- Upload and process documents (PDFs, Word, Excel, PowerPoint, images, and 15+ formats)
- Ask natural-language questions across uploaded documents
- Receive AI-generated answers with sentence-level citations traceable to the source document
- Detect inconsistencies across multiple documents
- Interact in 13+ languages with built-in translation and voice input

The Service uses a proprietary Knowledge Graph, large language models (LLMs), and retrieval-augmented generation (RAG) to provide answers. **Evidoc retrieves information from your documents — it does not generate facts independently.** However, AI systems may produce errors, and you should independently verify answers for critical decisions.

---

## 3. Eligibility

You must be at least 18 years old (or the age of majority in your jurisdiction) to use the Service. By using the Service, you represent and warrant that you meet this requirement.

---

## 4. Account Registration and Security

### 4.1 Account Creation

To use the Service, you must create an account via one of the following methods:
- **Individual accounts (B2C):** Self-service registration through Azure AD B2C / Entra External ID
- **Business accounts (B2B):** Azure Active Directory (Entra ID) with group-based access provisioned by your organization's administrator

### 4.2 Account Security

You are responsible for:
- Maintaining the confidentiality of your account credentials
- All activities that occur under your account
- Notifying us immediately at support@hulkdesign.com of any unauthorized use

We are not liable for any loss arising from unauthorized use of your account.

---

## 5. Subscription Plans and Billing

### 5.1 Plans

The Service is offered under the following tiers:

| Tier | Price | Monthly Credits | Queries/Month | Max Documents | Max Storage |
|------|-------|----------------|---------------|---------------|-------------|
| **Free** | $0 | 500 | 2,000 | 10 | 0.5 GB |
| **Pro** | $10/mo | 3,000 | 5,000 | 50 | 2 GB |
| **Pro Plus** | $39/mo | 15,000 | 20,000 | 500 | 10 GB |
| **Business** | $19/user/mo | 5,000 | 5,000 | 50 | 4 GB |
| **Enterprise** | $39/user/mo | 14,000 | 50,000 | Unlimited | 10 GB |

Plan features, pricing, and limits may change with prior notice. Current pricing is always available on the Service's pricing page.

### 5.2 Credits

The Service operates on a credit-based metering system. Credits are consumed by operations including AI queries, document processing (OCR), embedding generation, and translation. Credit costs vary by operation type. Unused credits do not roll over between billing periods.

### 5.3 Payment

Paid subscriptions are processed through **Stripe**. By subscribing to a paid plan, you agree to Stripe's terms of service. You authorize us to charge your payment method on a recurring basis until you cancel.

### 5.4 Cancellation and Refunds

- You may cancel your subscription at any time through the billing portal
- Cancellation takes effect at the end of the current billing period
- No prorated refunds are provided for partial billing periods
- Upon cancellation, your account reverts to the Free tier
- Your uploaded documents remain accessible for 30 days after downgrade; after that, documents exceeding the Free tier storage limit may be deleted

### 5.5 Rate Limits

Each plan includes daily and monthly query limits. When limits are exceeded, the Service returns an HTTP 429 response. Remaining quota is communicated via response headers. Rate limits reset at midnight UTC (daily) and on the billing cycle date (monthly).

---

## 6. Acceptable Use

### 6.1 You May

- Upload documents you own or have authorization to process
- Use the Service for lawful personal, professional, or business purposes
- Share answers and citations derived from your own documents

### 6.2 You May Not

- Upload documents containing illegal content, malware, or content that violates third-party rights
- Attempt to reverse-engineer, decompile, or extract the underlying models, algorithms, or Knowledge Graph logic
- Use the Service to generate content that is misleading, defamatory, or harmful
- Circumvent rate limits, quotas, or authentication mechanisms
- Share account credentials or allow unauthorized third parties to access your account
- Use automated scripts, bots, or scrapers to access the Service beyond provided APIs
- Resell, sublicense, or redistribute the Service without written consent
- Use the Service in any manner that could damage, disable, or impair it

Violation of these terms may result in immediate account suspension or termination.

---

## 7. Your Documents and Data

### 7.1 Ownership

**You retain full ownership of all documents you upload.** We claim no intellectual property rights over your content.

### 7.2 License to Process

By uploading documents, you grant us a limited, non-exclusive license to:
- Store your documents in encrypted cloud storage (Azure Blob Storage)
- Process documents through OCR and layout extraction (Azure Document Intelligence)
- Extract text, entities, and relationships to build a Knowledge Graph (stored in Neo4j)
- Generate embeddings for semantic search (via Voyage AI)
- Use document content to answer your queries via large language models (Azure OpenAI)

This license exists solely to provide the Service and is terminated when you delete your documents or your account.

### 7.3 Data Isolation

- **B2C accounts:** Your documents are isolated to your individual user account
- **B2B accounts:** Documents are isolated to your organization's assigned group/tenant
- Documents from different tenants are never mixed in queries or Knowledge Graph operations

### 7.4 Document Deletion

When you delete a document through the Service:
- The file is removed from blob storage
- Associated Knowledge Graph data (entities, relationships, sentences, embeddings) is removed from Neo4j
- Deletion is permanent and cannot be undone

### 7.5 No Training on Your Data

We do **not** use your uploaded documents or query content to train, fine-tune, or improve our AI models or any third-party models. Your documents are processed solely to serve your queries.

---

## 8. AI-Generated Outputs

### 8.1 Nature of Outputs

The Service provides AI-generated answers based on retrieval from your documents. While we employ deterministic retrieval methods and sentence-level citation to minimize errors:

- **AI outputs may contain inaccuracies, omissions, or misinterpretations**
- Citations link to source sentences but may not capture full context
- Cross-document inconsistency detection has a measured accuracy of 93.8% on our benchmark — it is not infallible

### 8.2 Not Professional Advice

Outputs from the Service do **not** constitute legal, financial, medical, regulatory, or any other professional advice. You should always consult qualified professionals before making decisions based on AI-generated outputs.

### 8.3 Your Responsibility

You are solely responsible for how you use, rely on, or distribute outputs from the Service. We are not liable for decisions made based on AI-generated answers.

---

## 9. Third-Party Services

The Service integrates with third-party services to deliver its functionality. By using the Service, you acknowledge that your data may be processed by:

| Provider | Purpose | Data Processed |
|----------|---------|----------------|
| **Microsoft Azure** | Cloud hosting, OCR, authentication, storage, translation, speech | Documents, account data, queries |
| **Azure OpenAI** | AI language model completions | Query text, document excerpts |
| **Voyage AI** | Semantic embeddings and reranking | Document text chunks |
| **Neo4j Aura** | Knowledge Graph storage | Extracted entities, relationships, text |
| **Stripe** | Payment processing | Payment method, billing address, email |
| **PostHog** (opt-in) | Product analytics | Usage events (no document content) |
| **Sentry** (opt-in) | Error tracking | Error metadata (PII stripped, no query text) |

Each provider is subject to their own terms of service and privacy policies. We select providers that maintain industry-standard security and data protection practices.

---

## 10. Intellectual Property

### 10.1 Our IP

The Service, including its Knowledge Graph architecture, retrieval algorithms, user interface, branding, and documentation, is the intellectual property of BangDesign Co. Ltd. and is protected by applicable copyright, trademark, and trade secret laws.

### 10.2 Feedback

If you provide suggestions, ideas, or feedback about the Service, you grant us a non-exclusive, royalty-free, perpetual license to use and incorporate that feedback without obligation to you.

---

## 11. Limitation of Liability

### 11.1 Disclaimer of Warranties

THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, WHETHER EXPRESS, IMPLIED, OR STATUTORY, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, ACCURACY, AND NON-INFRINGEMENT.

We do not warrant that:
- The Service will be uninterrupted, error-free, or secure
- AI-generated outputs will be accurate, complete, or suitable for any particular purpose
- All inconsistencies in your documents will be detected

### 11.2 Limitation

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, HULKDESIGN AI SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF PROFITS, DATA, USE, OR GOODWILL, ARISING FROM YOUR USE OF THE SERVICE.

OUR TOTAL AGGREGATE LIABILITY FOR ALL CLAIMS ARISING FROM OR RELATED TO THE SERVICE SHALL NOT EXCEED THE AMOUNT YOU PAID TO US IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM, OR USD $100, WHICHEVER IS GREATER.

---

## 12. Indemnification

You agree to indemnify, defend, and hold harmless BangDesign Co. Ltd., its officers, directors, employees, and agents from any claims, liabilities, damages, losses, or expenses (including reasonable legal fees) arising from:

- Your use of the Service
- Your violation of these Terms
- Your violation of any third-party rights, including intellectual property rights
- Documents you upload to the Service

---

## 13. Termination

### 13.1 By You

You may terminate your account at any time by contacting support@hulkdesign.com or through your account settings. Upon termination:
- Your subscription (if any) is cancelled
- You have 30 days to download your documents
- After 30 days, all your data (documents, Knowledge Graph data, chat history) is permanently deleted

### 13.2 By Us

We may suspend or terminate your account immediately and without notice if:
- You violate these Terms
- We are required to do so by law
- We discontinue the Service (with 60 days' advance notice when reasonably practicable)

### 13.3 Effect of Termination

Sections 7.1 (Ownership), 8 (AI-Generated Outputs), 10 (Intellectual Property), 11 (Limitation of Liability), 12 (Indemnification), and 14 (Governing Law) survive termination.

---

## 14. Governing Law and Dispute Resolution

### 14.1 Governing Law

These Terms shall be governed by and construed in accordance with the laws of the **Kingdom of Thailand**, without regard to conflict of law principles.

### 14.2 Dispute Resolution

Any dispute arising from these Terms or the Service shall first be attempted to be resolved through good-faith negotiation. If negotiation fails within 30 days, the dispute shall be submitted to the exclusive jurisdiction of the courts of Thailand.

### 14.3 Language

In the event of any conflict between the English version and any translated version of these Terms, the English version shall prevail.

---

## 15. Changes to These Terms

We may update these Terms from time to time. Material changes will be communicated via:
- Email notification to the address associated with your account
- A prominent notice within the Service

Continued use of the Service after changes take effect constitutes acceptance of the revised Terms. If you disagree with the changes, you may terminate your account as described in Section 13.

---

## 16. General Provisions

- **Entire Agreement:** These Terms, together with the Privacy Policy and Cookie Policy, constitute the entire agreement between you and BangDesign Co. Ltd. regarding the Service.
- **Severability:** If any provision of these Terms is found unenforceable, the remaining provisions remain in effect.
- **Waiver:** Failure to enforce any provision does not constitute a waiver of that provision.
- **Assignment:** You may not assign your rights under these Terms without our written consent. We may assign our rights without restriction.
- **Force Majeure:** We are not liable for delays or failures caused by events beyond our reasonable control.

---

## 17. Contact Us

For questions about these Terms:

**BangDesign Co. Ltd.**
Email: support@hulkdesign.com
Subject line: "Terms of Service Inquiry"

---

*These Terms of Service were last updated on 2026-03-20.*
