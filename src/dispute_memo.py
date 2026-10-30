"""
Automated Legal Freight Dispute Claim Notice & Memo Generator.
Generates NMFTA and SOX compliant legal claim notices for disputed carrier invoices.
"""
from typing import Dict, List, Any
import datetime

class DisputeMemoGenerator:
    @staticmethod
    def generate_memo(invoice_data: Dict[str, Any], exceptions: List[Dict[str, Any]], lines: List[Dict[str, Any]]) -> str:
        """Generate formal legal carrier dispute claim notice."""
        inv_id = invoice_data["invoice_id"]
        carrier_id = invoice_data["carrier_id"]
        shipment_id = invoice_data["shipment_id"]
        total_billed = float(invoice_data["total_billed_usd"])
        total_expected = float(invoice_data["total_expected_usd"])
        total_disputed = float(invoice_data["variance_usd"])
        
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%b-%Y %H:%M UTC")

        memo = f"""========================================================================================
                     FORMAL FREIGHT BILLING DISPUTE & AUDIT CLAIM NOTICE
========================================================================================
DATE OF NOTICE:          {now_str}
DISPUTE CLAIM REF:       CLM-{inv_id[-6:]}-DISPUTE
CARRIER IDENTIFIER:      {carrier_id}
CONTESTED INVOICE ID:    {inv_id}
REFERENCED SHIPMENT ID:  {shipment_id}
AUDIT VERDICT:           DISPUTED / PAYMENT HOLD ISSUED
----------------------------------------------------------------------------------------

1. FINANCIAL SETTLEMENT SUMMARY
   Total Billed by Carrier:        ${total_billed:>12,.2f}
   Contractually Approved Amount:  ${total_expected:>12,.2f}
   TOTAL CONTESTED / DISPUTED:     ${total_disputed:>12,.2f}

2. ITEM-LEVEL DISPUTE EXCEPTIONS & CONTRACTUAL VIOLATIONS
"""
        for idx, ex in enumerate(exceptions, 1):
            memo += f"""   [{idx}] EXCEPTION CODE:  {ex['exception_code']} (Severity: {ex['severity']})
       DISPUTED AMOUNT: ${float(ex['disputed_amount_usd']):,.2f}
       AUDIT FINDING:   {ex['explanation']}
"""

        memo += f"""
3. ITEMIZED CHARGE RECONCILIATION
   {'Line':<5} | {'Type':<18} | {'Code':<10} | {'Billed':<10} | {'Expected':<10} | {'Variance':<10} | {'Status':<15}
   {'-'*88}
"""
        for l in lines:
            memo += f"   {l['line_number']:<5} | {l['line_type']:<18} | {l['charge_code']:<10} | ${float(l['billed_amount_usd']):<9,.2f} | ${float(l.get('expected_amount_usd', 0.0)):<9,.2f} | ${float(l.get('variance_usd', 0.0)):<9,.2f} | {l['line_status']:<15}\n"

        memo += f"""
4. LEGAL DECLARATION & ACTION REQUIRED
   Pursuant to the Master Transportation Services Agreement and NMFTA uniform freight
   billing standards, payment for the contested amount of ${total_disputed:,.2f} has been
   placed on administrative hold pending resolution.
   
   Carrier is requested to:
   [a] Issue a formal Credit Memorandum (CR) reconciling the disputed ${total_disputed:,.2f}, OR
   [b] Submit proof of delivery (POD) records / contractual tariff documentation supporting
       the variance within 15 business days.

   AUTHORIZED SIGNATURE:
   Automated Freight Audit & Financial Recovery Platform
   Enterprise Logistics & Operations Directorate
========================================================================================
"""
        return memo
