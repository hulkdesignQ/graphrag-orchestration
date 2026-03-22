export const SAMPLE_FOLDER_NAME = "Sample Documents";

const SERVICE_AGREEMENT = `SERVICE AGREEMENT

Between: Acme Corporation ("Provider")
And: Greenfield Properties LLC ("Client")
Date: January 15, 2026
Agreement Number: SA-2026-0042

1. SCOPE OF SERVICES

The Provider shall deliver the following services to the Client:

a) Monthly property inspection of all units at 742 Evergreen Terrace Complex
b) Quarterly HVAC maintenance for 24 residential units
c) Emergency repair response within 4 business hours of notification
d) Annual fire safety system inspection and certification

2. PAYMENT TERMS

The Client shall pay the Provider according to the following schedule:

- Monthly inspection fee: $2,400 per month
- Quarterly HVAC maintenance: $1,800 per quarter
- Emergency repairs: $150 per hour, billed in 30-minute increments
- Annual fire safety inspection: $3,200 per inspection
- All invoices are due within 30 days of receipt
- Late payments incur a 1.5% monthly interest charge

3. TERM AND TERMINATION

This agreement is effective for 24 months from the date above.
Either party may terminate with 90 days written notice.
Early termination by the Client incurs a fee equal to 3 months of the monthly inspection rate.

4. LIABILITY AND INSURANCE

The Provider maintains general liability insurance of $2,000,000.
The Provider is not liable for pre-existing conditions not documented in the initial inspection report.

5. DISPUTE RESOLUTION

Any disputes shall be resolved through binding arbitration in accordance with the rules of the American Arbitration Association, held in Portland, Oregon.

Signed:
James Mitchell, CEO — Acme Corporation
Sarah Chen, Managing Director — Greenfield Properties LLC`;

const INVOICE = `INVOICE

From: Acme Corporation
123 Industrial Parkway, Suite 400
Portland, OR 97201

To: Greenfield Properties LLC
456 Commercial Drive
Portland, OR 97204

Invoice Number: INV-1042
Invoice Date: March 1, 2026
Due Date: March 31, 2026
Reference: Service Agreement SA-2026-0042

DESCRIPTION                                QTY      RATE        AMOUNT
------------------------------------------------------------------------
Monthly property inspection (Mar 2026)     1        $2,400.00   $2,400.00
Emergency repair - Unit 12B pipe burst     3 hrs    $150.00     $450.00
Emergency repair - Unit 7A electrical      1.5 hrs  $150.00     $225.00
Quarterly HVAC maintenance (Q1 2026)       1        $1,850.00   $1,850.00
------------------------------------------------------------------------
                                           Subtotal:            $4,925.00
                                           Tax (0%):            $0.00
                                           TOTAL DUE:           $4,925.00

Payment Terms: Net 30
Please remit payment to: Acme Corporation, Account #4420-8891

Notes:
- Emergency repair for Unit 12B was dispatched within 2 hours of notification
- HVAC maintenance completed for all 24 units on February 28, 2026
- Next quarterly HVAC maintenance scheduled for May 2026`;

const DATA_POLICY = `GREENFIELD PROPERTIES LLC
DATA HANDLING AND RETENTION POLICY

Document ID: POL-DH-2025-003
Effective Date: July 1, 2025
Last Reviewed: January 10, 2026
Approved By: Sarah Chen, Managing Director

1. PURPOSE

This policy establishes requirements for handling, storing, and disposing of tenant personal data and property records at Greenfield Properties LLC.

2. DATA CLASSIFICATION

2.1 Confidential: Tenant social security numbers, financial records, background check results
2.2 Internal: Lease agreements, maintenance records, vendor contracts, inspection reports
2.3 Public: Property listings, community notices, general company information

3. RETENTION PERIODS

- Lease agreements: 7 years after lease termination
- Tenant applications and screening: 3 years after decision
- Maintenance and repair records: 5 years from completion
- Financial records and invoices: 7 years per IRS requirements
- Insurance claims: 10 years from resolution
- Employee records: 7 years after termination of employment
- Vendor contracts: 7 years after contract expiration
- Inspection reports: Life of the property

4. DATA STORAGE

All confidential data must be stored in encrypted systems with access logging.
Physical documents containing confidential data must be stored in locked cabinets.
Cloud storage must use providers certified for SOC 2 Type II compliance.

5. DATA DISPOSAL

Confidential documents must be cross-cut shredded.
Electronic records must be securely wiped using NIST 800-88 guidelines.
Disposal of confidential data must be logged with date, method, and responsible party.

6. BREACH NOTIFICATION

In the event of a data breach involving tenant personal information:
- Internal notification to Managing Director within 4 hours
- Affected tenants notified within 72 hours
- State attorney general notified as required by Oregon data breach notification law
- Breach response documented and retained for 10 years

7. THIRD-PARTY ACCESS

Vendors and contractors may access Internal data only as needed for service delivery.
Access to Confidential data requires a signed data processing agreement.
All third-party access must be logged and reviewed quarterly.`;

export interface SampleDocument {
    name: string;
    content: string;
}

export const SAMPLE_DOCUMENTS: SampleDocument[] = [
    { name: "Acme_Service_Agreement.txt", content: SERVICE_AGREEMENT },
    { name: "Acme_Invoice_1042.txt", content: INVOICE },
    { name: "Greenfield_Data_Policy.txt", content: DATA_POLICY },
];

export function createSampleFiles(): File[] {
    return SAMPLE_DOCUMENTS.map(
        doc => new File([doc.content], doc.name, { type: "text/plain" })
    );
}
