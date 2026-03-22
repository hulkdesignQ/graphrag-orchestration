# Data Processing Agreement

**Effective Date:** March 28, 2026
**Last Updated:** 2026-03-22

---

## 1. Introduction

This Data Processing Agreement ("DPA") forms part of the agreement between the entity accepting this DPA ("Controller", "you", or "your") and **BangDesign Co. Ltd.** ("Processor", "we", "us", or "our") for the provision of the **Evidoc** service ("Service") — an AI-powered document intelligence platform.

This DPA reflects the parties' commitment to comply with applicable data protection laws, including the **EU General Data Protection Regulation** (Regulation 2016/679, "GDPR") and the **Thailand Personal Data Protection Act** B.E. 2562 ("PDPA"), with respect to the processing of Personal Data by the Processor on behalf of the Controller.

This DPA is incorporated into and subject to the terms of the [Terms of Service](./TERMS_OF_SERVICE.md) or other written agreement between the parties governing the use of the Service (the "Main Agreement"). In the event of a conflict between this DPA and the Main Agreement, this DPA shall prevail with respect to data protection matters.

---

## 2. Definitions

For the purposes of this DPA, the following terms shall have the meanings set out below. Capitalized terms not defined herein shall have the meanings given in the Main Agreement or applicable data protection law.

| Term | Definition |
|------|-----------|
| **Controller** | The entity that determines the purposes and means of the processing of Personal Data — i.e., the customer using the Service. |
| **Processor** | BangDesign Co. Ltd., which processes Personal Data on behalf of the Controller to provide the Service. |
| **Personal Data** | Any information relating to an identified or identifiable natural person ("Data Subject"). |
| **Processing** | Any operation performed on Personal Data, including collection, recording, storage, retrieval, use, disclosure, erasure, or destruction. |
| **Data Subject** | An identified or identifiable natural person whose Personal Data is processed. |
| **Sub-processor** | A third party engaged by the Processor to process Personal Data on behalf of the Controller. |
| **Data Breach** | A breach of security leading to the accidental or unlawful destruction, loss, alteration, unauthorized disclosure of, or access to, Personal Data. |
| **DSAR** | A Data Subject Access Request — any request made by a Data Subject to exercise their rights under applicable data protection law. |
| **Standard Contractual Clauses (SCCs)** | The contractual clauses approved by the European Commission for international transfers of Personal Data. |

---

## 3. Scope and Purpose of Processing

### 3.1 Scope

This DPA applies to all Personal Data that the Processor processes on behalf of the Controller in connection with the provision of the Service. The Processor shall process Personal Data only to the extent necessary to provide, maintain, and improve the Service as described in the Main Agreement.

### 3.2 Purpose

The Processor processes Personal Data for the following purposes:

- Providing the Evidoc document intelligence platform, including document upload, processing, analysis, and retrieval
- Processing documents using Knowledge Graph technology, Large Language Models (LLMs), and Retrieval-Augmented Generation (RAG)
- Storing and indexing document content and metadata for search and retrieval
- Authenticating and managing user accounts
- Generating usage analytics and audit logs
- Providing customer support

### 3.3 No Use for Model Training

We do **not** use your documents or Personal Data to train, fine-tune, or improve any AI or machine learning models. Document content is processed solely to provide the Service to you.

---

## 4. Duration of Processing

This DPA shall remain in effect for the duration of the Main Agreement. Processing of Personal Data shall commence upon the effective date of the Main Agreement and shall continue until the Main Agreement is terminated or expires, subject to the data deletion provisions in [Section 14](#14-termination-and-data-deletion) of this DPA.

---

## 5. Types of Personal Data Processed

The Processor may process the following types of Personal Data on behalf of the Controller:

| Category | Examples |
|----------|----------|
| **Document Content** | Text, images, tables, and other content within uploaded documents (PDFs, Word, Excel, images, and 15+ supported formats). May contain Personal Data depending on the documents uploaded by the Controller. |
| **Document Metadata** | File names, file types, upload timestamps, file sizes, folder assignments, and processing status. |
| **Account Data** | User names, email addresses, organizational identifiers, authentication tokens, and role assignments. |
| **Usage Logs** | Access timestamps, queries submitted, features used, API calls, and session identifiers. |
| **Payment Data** | Billing contact information and subscription details. Payment card data is processed directly by Stripe and is **not** stored by the Processor. |

---

## 6. Categories of Data Subjects

The Personal Data processed under this DPA may relate to the following categories of Data Subjects:

- **Controller's employees and staff** — users with accounts on the Service
- **Controller's clients and customers** — individuals whose data may appear in documents uploaded to the Service
- **Controller's end users** — individuals who interact with the Service on behalf of the Controller
- **Other individuals** — any person whose Personal Data is contained within documents uploaded by the Controller

The Controller is responsible for ensuring it has a lawful basis to upload and process documents containing Personal Data of these Data Subjects.

---

## 7. Obligations of the Processor

### 7.1 Processing on Instructions

The Processor shall process Personal Data only on documented instructions from the Controller, including with regard to transfers of Personal Data to a third country, unless required to do so by applicable law. In such a case, the Processor shall inform the Controller of that legal requirement before processing, unless the law prohibits such notification.

### 7.2 Confidentiality

The Processor shall ensure that all personnel authorized to process Personal Data have committed themselves to confidentiality or are under an appropriate statutory obligation of confidentiality. Access to Personal Data is restricted to personnel who require it to perform their duties in connection with the Service.

### 7.3 Security Measures

The Processor shall implement and maintain appropriate technical and organizational measures to ensure a level of security appropriate to the risk, as described in [Annex A](#annex-a-technical-and-organizational-security-measures) of this DPA. These measures include, but are not limited to:

- Encryption of data at rest and in transit
- Access controls and authentication mechanisms
- Data isolation between Controller tenants
- Regular security assessments and updates

### 7.4 Sub-processors

The Processor shall not engage a Sub-processor without the prior written consent of the Controller. The Controller provides general authorization for the Sub-processors listed in [Section 8](#8-sub-processors). The Processor shall notify the Controller of any intended changes to the list of Sub-processors, providing at least **30 days' prior written notice** to allow the Controller to object. If the Controller objects on reasonable grounds, the parties shall work in good faith to resolve the objection.

### 7.5 Assistance with Data Subject Rights

The Processor shall assist the Controller in responding to DSARs by appropriate technical and organizational measures, insofar as this is possible. See [Section 12](#12-data-subject-rights) for details.

### 7.6 Assistance with Compliance

The Processor shall assist the Controller in ensuring compliance with obligations under Articles 32 to 36 of the GDPR (security, breach notification, data protection impact assessments, and prior consultation), taking into account the nature of processing and the information available to the Processor.

### 7.7 Data Deletion or Return

Upon termination of the Main Agreement, the Processor shall, at the Controller's choice, delete or return all Personal Data and delete existing copies, unless applicable law requires storage of the Personal Data. See [Section 14](#14-termination-and-data-deletion) for details.

### 7.8 Audit and Information

The Processor shall make available to the Controller all information necessary to demonstrate compliance with this DPA and allow for and contribute to audits, including inspections, conducted by the Controller or another auditor mandated by the Controller. See [Section 13](#13-audit-rights) for details.

### 7.9 Data Breach Notification

The Processor shall notify the Controller of any Data Breach without undue delay and in any event within **72 hours** of becoming aware of the breach. See [Section 11](#11-data-breach-notification) for details.

---

## 8. Sub-processors

The Controller provides general authorization for the Processor to engage the following Sub-processors:

| Sub-processor | Purpose | Location | Data Handling Notes |
|--------------|---------|----------|-------------------|
| **Microsoft Azure** | Cloud infrastructure, compute, storage (Azure Cosmos DB, Azure Blob Storage), authentication (Azure AD / Entra ID, Azure AD B2C) | West Europe | Data encrypted at rest and in transit. Primary hosting region. |
| **Neo4j Aura** | Graph database for knowledge graph storage and vector embeddings | Managed (GCP/Azure) | Stores graph relationships and embeddings derived from documents. |
| **OpenAI / Azure OpenAI** | Large Language Model (LLM) processing for document analysis and query answering | Azure infrastructure | **No data retention** — inputs and outputs are not stored or used for model training. |
| **Voyage AI** | Embedding generation and reranking for document retrieval | Cloud-hosted | **No data retention** — inputs and outputs are not stored or used for model training. |
| **Stripe** | Payment processing and subscription management | United States / Global | PCI DSS Level 1 certified. Processes billing data only — no access to document content. |
| **Formspree** | Contact form submission handling | United States | Processes contact inquiries only — **no access to document data or content**. |

### 8.1 Changes to Sub-processors

The Processor shall notify the Controller by email at least **30 days** before authorizing any new Sub-processor to process Personal Data. The notification shall include the Sub-processor's name, purpose, and location.

If the Controller raises a reasonable objection within the 30-day notice period, the Processor shall work with the Controller to find an alternative solution. If no resolution can be reached, the Controller may terminate the affected Service without penalty.

### 8.2 Sub-processor Obligations

The Processor shall impose data protection obligations on each Sub-processor that are no less protective than those set out in this DPA. The Processor shall remain liable for the acts and omissions of its Sub-processors.

---

## 9. International Data Transfers

### 9.1 Primary Hosting

The Service is primarily hosted on Microsoft Azure in the **West Europe** region. The Processor endeavors to keep Personal Data within the European Economic Area (EEA) and jurisdictions with adequate data protection where feasible.

### 9.2 Transfer Mechanisms

Where Personal Data is transferred to a country outside the EEA that has not been recognized by the European Commission as providing an adequate level of data protection, the Processor shall ensure that appropriate safeguards are in place, including:

- **Standard Contractual Clauses (SCCs)** approved by the European Commission
- Binding Corporate Rules where applicable
- Any other transfer mechanism recognized under applicable data protection law

### 9.3 Thailand PDPA Compliance

For transfers of Personal Data originating from Thailand, the Processor shall ensure compliance with the cross-border transfer requirements under the PDPA, including ensuring that the destination country has adequate data protection standards or that appropriate safeguards are in place.

---

## 10. Controller Obligations

The Controller shall:

- Ensure it has a lawful basis for processing Personal Data and for instructing the Processor to process Personal Data on its behalf
- Ensure that documents uploaded to the Service do not contain Personal Data that the Controller is not authorized to process
- Provide clear and documented instructions to the Processor regarding the processing of Personal Data
- Comply with its obligations under applicable data protection law, including providing notice to Data Subjects and responding to DSARs
- Promptly notify the Processor of any changes to applicable data protection requirements that may affect the Processor's obligations

---

## 11. Data Breach Notification

### 11.1 Notification to Controller

The Processor shall notify the Controller without undue delay, and in any event within **72 hours** of becoming aware of a Data Breach affecting Personal Data processed on behalf of the Controller. The notification shall include, to the extent available:

- A description of the nature of the Data Breach, including the categories and approximate number of Data Subjects and records concerned
- The name and contact details of the Processor's point of contact for further information
- A description of the likely consequences of the Data Breach
- A description of the measures taken or proposed to address the Data Breach, including measures to mitigate its possible adverse effects

### 11.2 Assistance

The Processor shall cooperate with the Controller and take reasonable steps to assist in the investigation, mitigation, and remediation of the Data Breach. The Processor shall also assist the Controller in fulfilling its obligation to notify supervisory authorities and Data Subjects, where required by applicable law.

### 11.3 Contact

Data breach notifications shall be sent to the Controller's designated contact. Controllers may reach the Processor's security team at **support@hulkdesign.com** with the subject line "Data Breach Notification".

---

## 12. Data Subject Rights

### 12.1 Controller Responsibility

The Controller is responsible for handling all DSARs received from Data Subjects, including requests for access, rectification, erasure, restriction, portability, and objection.

### 12.2 Processor Assistance

The Processor shall assist the Controller in responding to DSARs by:

- Providing technical mechanisms to export, correct, or delete Personal Data within the Service
- Responding to Controller requests related to DSARs within a reasonable timeframe
- Forwarding any DSARs received directly by the Processor to the Controller without undue delay

### 12.3 Fees

Where the Processor incurs significant costs in assisting with DSARs beyond the normal functionality of the Service, the Processor may charge a reasonable fee for such assistance, agreed upon in advance with the Controller.

---

## 13. Audit Rights

### 13.1 Right to Audit

The Controller may audit the Processor's compliance with this DPA **once per calendar year**, subject to the following conditions:

- The Controller shall provide at least **30 days' prior written notice** of the audit
- The audit shall be conducted during normal business hours and shall not unreasonably interfere with the Processor's operations
- The Controller (or its mandated auditor) shall be bound by confidentiality obligations
- The audit scope shall be limited to the Processor's processing activities relating to the Controller's Personal Data

### 13.2 Third-Party Certifications

The Processor may satisfy audit requests by providing relevant third-party certifications, audit reports (such as SOC 2 or ISO 27001), or other evidence of compliance, where available. The Controller shall consider such documentation before requiring an on-site audit.

### 13.3 Costs

Each party shall bear its own costs in connection with audits. If an audit requires significant dedicated resources from the Processor beyond providing existing documentation, the parties shall agree on a reasonable allocation of costs in advance.

---

## 14. Termination and Data Deletion

### 14.1 Effect of Termination

Upon termination or expiration of the Main Agreement, the Processor shall cease all processing of Personal Data on behalf of the Controller, except as required by applicable law.

### 14.2 Data Return or Deletion

Within **30 days** of termination, the Processor shall, at the Controller's written request:

- **Return** all Personal Data to the Controller in a commonly used, machine-readable format; or
- **Delete** all Personal Data, including all copies, from the Processor's systems and those of its Sub-processors

If the Controller does not provide instructions within 30 days of termination, the Processor shall delete all Personal Data.

### 14.3 Certification

Upon request, the Processor shall provide written certification that all Personal Data has been deleted in accordance with this Section.

### 14.4 Legal Retention

The Processor may retain Personal Data to the extent required by applicable law, provided that the Processor shall ensure the confidentiality of such data and shall process it only for the purposes required by law.

---

## 15. Liability

### 15.1 Limitations

The liability of each party under this DPA shall be subject to the limitations and exclusions of liability set out in the Main Agreement, except where applicable law prohibits such limitations with respect to data protection obligations.

### 15.2 Indemnification

Each party shall indemnify the other against any costs, claims, damages, or expenses incurred as a result of any breach of this DPA or applicable data protection law by the indemnifying party.

---

## 16. Governing Law and Dispute Resolution

This DPA shall be governed by and construed in accordance with the laws of the **Kingdom of Thailand**, consistent with the Main Agreement. Any dispute arising out of or in connection with this DPA shall be resolved in accordance with the dispute resolution provisions of the Main Agreement.

---

## 17. General Provisions

### 17.1 Amendments

This DPA may be amended only by written agreement signed by both parties, except that the Processor may update the list of Sub-processors in accordance with [Section 8.1](#81-changes-to-sub-processors).

### 17.2 Severability

If any provision of this DPA is found to be invalid or unenforceable, the remaining provisions shall continue in full force and effect.

### 17.3 Entire Agreement

This DPA, together with the Main Agreement and the [Privacy Policy](./PRIVACY_POLICY.md), constitutes the entire agreement between the parties with respect to the processing of Personal Data.

### 17.4 Contact

For questions about this DPA, please contact us at **support@hulkdesign.com** with the subject line "Data Processing Agreement".

---

## Annex A: Technical and Organizational Security Measures

The Processor maintains the following technical and organizational security measures to protect Personal Data:

### A.1 Encryption

| Measure | Details |
|---------|---------|
| **Encryption at rest** | Azure Storage encryption (AES-256) for documents in Azure Blob Storage. Azure Cosmos DB encryption at rest for metadata. Neo4j Aura encryption at rest for graph data and embeddings. |
| **Encryption in transit** | TLS 1.2 or higher for all data in transit between clients, services, and Sub-processors. |

### A.2 Access Controls

| Measure | Details |
|---------|---------|
| **Authentication** | Azure AD / Entra ID for B2B authentication. Azure AD B2C for B2C authentication. Multi-factor authentication supported. |
| **Authorization** | Role-Based Access Control (RBAC) enforced at the application level. Group-based data isolation ensures users can only access documents within their authorized scope. |
| **Data isolation** | Folder-level isolation and group-based access control. **No cross-tenant data access** — each Controller's data is logically separated from other Controllers' data. |
| **Administrative access** | Restricted to authorized Processor personnel on a need-to-know basis. |

### A.3 Infrastructure Security

| Measure | Details |
|---------|---------|
| **Hosting** | Microsoft Azure (West Europe region) with Azure's built-in physical and network security controls. |
| **Network security** | Azure networking security features including network security groups and firewall rules. |
| **Security updates** | Regular application of security patches and updates to infrastructure and application components. |

### A.4 AI and Document Processing

| Measure | Details |
|---------|---------|
| **No model training** | User documents are **never** used for AI model training, fine-tuning, or improvement of third-party models. |
| **LLM data handling** | Document content sent to LLM providers (OpenAI / Azure OpenAI) is not retained by the provider and is not used for model training. |
| **Embedding data handling** | Document content sent to Voyage AI for embedding generation is not retained and is not used for model training. |

### A.5 Organizational Measures

| Measure | Details |
|---------|---------|
| **Personnel confidentiality** | All personnel with access to Personal Data are bound by confidentiality obligations. |
| **Access reviews** | Regular reviews of access permissions to ensure least-privilege principles are maintained. |
| **Incident response** | Documented incident response procedures for Data Breach detection, assessment, and notification. |

---

*This Data Processing Agreement was last updated on 2026-03-22.*
