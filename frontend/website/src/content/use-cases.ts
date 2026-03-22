export interface UseCase {
  slug: string;
  badge: string;
  heroTitle: string;
  heroSubtitle: string;
  painPoints: { title: string; desc: string }[];
  howEvidocHelps: { title: string; desc: string }[];
  exampleQueries: { question: string; context: string }[];
  testimonial?: { quote: string; author: string };
  ctaText: string;
}

export const useCases: Record<string, UseCase> = {
  legal: {
    slug: "legal",
    badge: "Legal",
    heroTitle: "Stop reading contracts.<br>Start asking them.",
    heroSubtitle: "Review entire contract portfolios in minutes. Every clause cited to the exact sentence — click to verify on the original page.",
    painPoints: [
      {
        title: "Contract review takes weeks",
        desc: "Paralegals manually read through hundreds of contracts looking for specific clauses. A single portfolio review can take 6–12 weeks.",
      },
      {
        title: "Ctrl+F misses what matters",
        desc: '"Change of control" might be written as "transfer of ownership," "assignment of rights," or buried in a definition section. Keyword search can\'t find what it can\'t predict.',
      },
      {
        title: "AI summaries you can't cite",
        desc: "ChatGPT will summarize your contract — but when opposing counsel asks \"where does it say that?\", you're back to manual search.",
      },
      {
        title: "Cross-referencing is error-prone",
        desc: "The master agreement says one thing, the amendment says another, and the side letter contradicts both. Finding these inconsistencies manually is where mistakes happen.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Ask across your entire portfolio",
        desc: "Upload 500 contracts. Ask one question. Evidoc finds every relevant clause across every document — cited to the exact sentence.",
      },
      {
        title: "Click any citation to verify",
        desc: "Every answer includes numbered citations. Click one — the original PDF opens with the exact sentence highlighted. Verification in seconds, not hours.",
      },
      {
        title: "Catch inconsistencies automatically",
        desc: "\"Do the amendment terms match the master agreement?\" Evidoc cross-references both documents and cites every discrepancy.",
      },
      {
        title: "Understands legal language",
        desc: "\"Acme Corp,\" \"Acme Corporation,\" and \"the Seller\" — Evidoc links them automatically. It reads like a lawyer, not a search engine.",
      },
    ],
    exampleQueries: [
      { question: "Which contracts have a change-of-control clause?", context: "Across a 200-contract portfolio — every relevant clause cited in seconds." },
      { question: "What are the termination provisions in the Acme agreement?", context: "Every termination-related clause, including those in amendments and side letters." },
      { question: "Do the indemnification terms differ between the US and EU contracts?", context: "Cross-document comparison with cited differences from both versions." },
      { question: "Which contracts expire in the next 90 days?", context: "Date extraction across all documents with links to the exact clause." },
      { question: "Are there any non-compete obligations that survive termination?", context: "Finds survival clauses even when phrased differently across agreements." },
    ],
    testimonial: {
      quote: "We used to spend 3 days cross-referencing contracts. Now we ask one question and get every relevant clause — cited to the exact sentence.",
      author: "Early Access User, Legal Operations",
    },
    ctaText: "Try Evidoc Free for Legal",
  },

  finance: {
    slug: "finance",
    badge: "Finance & Procurement",
    heroTitle: "Every invoice checked.<br>Every discrepancy cited.",
    heroSubtitle: "Match invoices against contracts, catch overcharges, and prepare audit responses — with proof you can click.",
    painPoints: [
      {
        title: "Invoice verification is manual",
        desc: "Procurement teams compare invoices against contracts line by line. At 500+ invoices per month, overcharges slip through — costing an average of $230K annually.",
      },
      {
        title: "Auditors want proof, not summaries",
        desc: "When the auditor asks \"where does it say the rate is $150/hour?\", you need the exact clause — not a ChatGPT summary.",
      },
      {
        title: "Financial records span dozens of documents",
        desc: "The contract, the amendments, the purchase orders, the invoices, the credit notes — the answer is spread across 20 documents in 3 different formats.",
      },
      {
        title: "Month-end close takes too long",
        desc: "Reconciling financial records, verifying charges, and preparing documentation for review — it's accurate but painfully slow.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Compare invoices to contracts instantly",
        desc: "\"Do these invoices match the agreed contract rates?\" Upload both — Evidoc cites every discrepancy with the exact rate from each document.",
      },
      {
        title: "Audit-ready answers in seconds",
        desc: "Every answer traces to the source. When the auditor asks, you click the citation — the original document opens with the relevant sentence highlighted.",
      },
      {
        title: "Cross-reference across document types",
        desc: "Contracts, amendments, POs, invoices, credit notes — Evidoc connects them all. One question spans everything.",
      },
      {
        title: "Catch what humans miss",
        desc: "\"Acme\" on the invoice and \"ACME Corporation\" in the contract? Same entity, linked automatically. Rate changes in amendment #3? Found and cited.",
      },
    ],
    exampleQueries: [
      { question: "Do these invoices match the contract terms?", context: "Every rate, quantity, and term compared — discrepancies cited from both documents." },
      { question: "What is the agreed hourly rate for emergency repairs?", context: "Finds the exact clause, even if the rate changed in an amendment." },
      { question: "Which invoices exceed the approved budget?", context: "Cross-references PO amounts against invoice totals with cited sources." },
      { question: "What are the payment terms across all vendor contracts?", context: "Net 30, Net 60, early payment discounts — all extracted and cited." },
      { question: "Have any vendors changed their rates in the last 12 months?", context: "Compares original agreements against amendments and latest invoices." },
    ],
    ctaText: "Try Evidoc Free for Finance",
  },

  compliance: {
    slug: "compliance",
    badge: "Compliance & Audit",
    heroTitle: "When the auditor asks,<br>answer in seconds.",
    heroSubtitle: "Find exactly where your policies address any requirement — cited to the sentence, highlighted on the original page.",
    painPoints: [
      {
        title: "Audit prep takes days",
        desc: "\"Where do your policies address data retention?\" The compliance team spends 3 days searching across 40+ policy documents to build the response.",
      },
      {
        title: "Policies are scattered",
        desc: "The data policy says one thing, the employee handbook says another, and the SOC 2 documentation references a third version. Which one is current?",
      },
      {
        title: "Gap analysis is manual",
        desc: "Comparing your policies against a new regulation or standard means reading every policy document and manually mapping requirements. For a team of 3, that's weeks.",
      },
      {
        title: "Proving compliance needs evidence",
        desc: "The auditor doesn't want a summary. They want the exact policy language, the exact version, in the exact document. Screenshots and manual highlights aren't scalable.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Answer audit questions instantly",
        desc: "\"Where do our policies address data retention?\" — Evidoc finds every relevant policy statement across all documents, cited to the exact sentence.",
      },
      {
        title: "Clickable evidence for auditors",
        desc: "Share the answer with citations. The auditor clicks — sees the exact sentence highlighted on the original policy document. No back-and-forth.",
      },
      {
        title: "Policy gap analysis in minutes",
        desc: "Upload the new regulation and your existing policies. Ask \"Which requirements aren't addressed in our current policies?\" — gaps cited from both sides.",
      },
      {
        title: "Track policy consistency",
        desc: "\"Does the employee handbook align with our data policy on retention periods?\" Evidoc finds inconsistencies across documents and cites both versions.",
      },
    ],
    exampleQueries: [
      { question: "Where do our policies address data retention?", context: "Every retention-related clause across all policy documents, with exact citations." },
      { question: "Which SOPs need updating for the new ISO standard?", context: "Gap analysis between current SOPs and the new standard, with both sides cited." },
      { question: "What is our breach notification timeline?", context: "Finds the notification requirements across privacy policy, incident response plan, and contracts." },
      { question: "Do our vendor agreements include data processing clauses?", context: "Reviews all vendor contracts for DPA language, citing present and missing clauses." },
      { question: "What employee training is required by our policies?", context: "Extracts all training requirements across handbook, security policy, and compliance docs." },
    ],
    testimonial: {
      quote: "Our last SOC 2 audit prep went from 2 weeks to 2 days. Every auditor question answered with the exact policy language, cited and clickable.",
      author: "Early Access User, Compliance Manager",
    },
    ctaText: "Try Evidoc Free for Compliance",
  },

  research: {
    slug: "research",
    badge: "Research & Academia",
    heroTitle: "Read 50 papers.<br>Or ask them one question.",
    heroSubtitle: "Synthesize findings across research papers, clinical studies, and technical reports — every claim traced to the source.",
    painPoints: [
      {
        title: "Literature reviews take weeks",
        desc: "Reading 50 papers to understand the state of research on a topic. Highlighting, note-taking, cross-referencing — it's thorough but painfully slow.",
      },
      {
        title: "Findings are buried in context",
        desc: "The key result is on page 14 of paper #37, but it contradicts a finding on page 8 of paper #12. You only discover this after reading both completely.",
      },
      {
        title: "Citation tracking is manual",
        desc: "You remember reading something relevant but can't remember which paper. Now you're re-reading 20 papers to find one sentence.",
      },
      {
        title: "AI summaries lose the nuance",
        desc: "ChatGPT summarizes a paper but misses the caveats. \"Effective in 80% of cases\" becomes \"effective\" — and you can't verify without re-reading.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Ask across your entire corpus",
        desc: "Upload 50 papers. Ask \"What do these studies say about treatment X?\" — consolidated findings from every paper, each cited to the exact sentence.",
      },
      {
        title: "Every claim is traceable",
        desc: "\"Paper 12, page 8, paragraph 3\" — click the citation and see the exact sentence highlighted. No ambiguity about what the original paper actually said.",
      },
      {
        title: "Find contradictions automatically",
        desc: "\"Do any of these papers disagree on the effectiveness of method Y?\" — Evidoc finds conflicting findings and cites both sides.",
      },
      {
        title: "Works across document types",
        desc: "PDFs, Word docs, spreadsheets with data tables, scanned historical papers — all connected, all searchable, all cited.",
      },
    ],
    exampleQueries: [
      { question: "What do these papers say about the efficacy of treatment X?", context: "Consolidated findings across 50 papers with individual citations for each claim." },
      { question: "Which studies report adverse effects?", context: "Every mention of adverse effects, side effects, or negative outcomes — cited per paper." },
      { question: "How do sample sizes compare across these studies?", context: "Extracts methodology details from each paper with cited sources." },
      { question: "Do any papers contradict the findings of Smith et al. 2024?", context: "Finds conflicting conclusions and cites the specific passages from each paper." },
      { question: "What research gaps are identified across this literature?", context: "Compiles future work and limitation sections from all papers." },
    ],
    ctaText: "Try Evidoc Free for Research",
  },

  realestate: {
    slug: "real-estate",
    badge: "Real Estate & Property",
    heroTitle: "Every clause. Every counter-offer.<br>Cross-referenced.",
    heroSubtitle: "Compare offers, review leases, and catch discrepancies across property documents — with proof on every answer.",
    painPoints: [
      {
        title: "Offer comparisons are tedious",
        desc: "Three counter-offers, each 30 pages. What changed? Agents compare them manually, paragraph by paragraph, hoping they don't miss a revised term.",
      },
      {
        title: "Lease portfolios are unmanageable",
        desc: "A property management firm with 200 leases can't quickly answer \"Which leases allow subletting?\" without reading every single one.",
      },
      {
        title: "Inspection reports pile up",
        desc: "Annual inspections, maintenance records, contractor reports — they're filed but never cross-referenced. Patterns go unnoticed until they become problems.",
      },
      {
        title: "Due diligence is a time crunch",
        desc: "Acquiring a property? Environmental reports, title documents, zoning records, lease abstracts — all need reviewing under a tight deadline.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Compare documents instantly",
        desc: "Upload the original offer and counter-offer. Ask \"What changed?\" — every difference cited from both versions.",
      },
      {
        title: "Search across your lease portfolio",
        desc: "\"Which leases have a pet policy?\" \"What's the average rent escalation clause?\" One question across 200 leases, every answer cited.",
      },
      {
        title: "Connect maintenance history",
        desc: "Upload inspection reports, contractor invoices, and service agreements. Ask \"Has the HVAC system been serviced per the contract terms?\"",
      },
      {
        title: "Accelerate due diligence",
        desc: "Upload the entire document package. Ask questions as you go — every answer traces to the source document. Due diligence in days, not weeks.",
      },
    ],
    exampleQueries: [
      { question: "What changed in the counter-offer?", context: "Every revised term, added clause, and removed condition — cited from both versions." },
      { question: "Which leases expire in the next 6 months?", context: "Expiration dates extracted from all leases with renewal terms cited." },
      { question: "Do the inspection reports flag any recurring issues?", context: "Patterns across years of reports, each occurrence cited." },
      { question: "What are the CAM charges across all commercial leases?", context: "Common Area Maintenance terms compared across the portfolio." },
      { question: "Are there any environmental concerns in the due diligence package?", context: "Findings from environmental reports, surveys, and assessments — all cited." },
    ],
    ctaText: "Try Evidoc Free for Real Estate",
  },

  personal: {
    slug: "personal",
    badge: "Personal & Everyday",
    heroTitle: "Your documents,<br>finally readable.",
    heroSubtitle: "Insurance policies, tax documents, medical records — ask a question in plain language, get an answer you can trust.",
    painPoints: [
      {
        title: "Insurance policies are unreadable",
        desc: "80 pages of legalese. You need to know if your roof is covered, but the answer is buried in exclusions, sub-limits, and defined terms that reference other sections.",
      },
      {
        title: "Tax documents are confusing",
        desc: "W-2s, 1099s, deduction receipts — you know the information is there, but finding the specific number you need takes longer than it should.",
      },
      {
        title: "Medical records are scattered",
        desc: "Lab results from one provider, specialist notes from another, imaging reports from a third. Getting a complete picture means reading everything.",
      },
      {
        title: "Legal agreements are intimidating",
        desc: "Rental agreements, employment contracts, loan documents — you signed them but aren't entirely sure what you agreed to.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Ask in plain language",
        desc: "\"Does my insurance cover water damage?\" — Evidoc finds the relevant coverage, exclusions, and limits, cited to the exact policy language.",
      },
      {
        title: "Verify every answer",
        desc: "Don't take the AI's word for it. Click the citation — see the exact sentence highlighted on the original document. You decide if it's right.",
      },
      {
        title: "Upload anything",
        desc: "PDFs, scanned documents, photos of paperwork — Evidoc reads them all. 15+ formats supported.",
      },
      {
        title: "13 languages supported",
        desc: "Ask in your language. Evidoc auto-detects and responds in kind — with voice input for hands-free use.",
      },
    ],
    exampleQueries: [
      { question: "What does my insurance actually cover?", context: "Coverage, exclusions, deductibles, and limits — all cited from your policy." },
      { question: "What's my deductible for emergency room visits?", context: "Finds the exact amount with the specific policy clause." },
      { question: "Can my landlord raise the rent before the lease ends?", context: "Rent adjustment clauses cited from your lease agreement." },
      { question: "What are the penalties for early loan repayment?", context: "Prepayment terms from your loan agreement, cited to the exact section." },
      { question: "What did my doctor recommend at the last visit?", context: "Extracts recommendations from visit notes with exact citations." },
    ],
    ctaText: "Try Evidoc Free",
  },
};

export const useCaseOrder = ["legal", "finance", "compliance", "research", "realestate", "personal"];
