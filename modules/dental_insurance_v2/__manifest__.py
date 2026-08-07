{
    'name': 'Dental Insurance v2',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Extends dental insurance with pre-auth document attachments, payer-specific claim templates and batch submission.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_insurance',
    ],
    'data': [
        'views/claim_v2_views.xml',
        'report/claim_form_report.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Insurance v2 — Pre-Auth & Claim Templates\n==================================================\nAdvanced insurance module building on Dental Insurance (dental_insurance).\n\nAdded Features\n--------------\n- Document attachments on pre-authorisation requests (referral letters, X-rays, notes)\n- Payer-specific printable claim templates (configurable per insurance company)\n- Batch claim submission — submit multiple claims to one payer in a single action\n- Claim response import — upload payer response file to auto-update claim statuses\n- EOB (Explanation of Benefits) attachment storage\n- Rejection reason codes with re-submission workflow\n- Insurance revenue vs collected reconciliation report\n\nRequires: dental_insurance\n',
    'price': 0,
    'currency': 'USD',
}
