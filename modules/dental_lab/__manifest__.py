{
    'name': 'Dental Lab Work Orders',
    'version': '18.0.1.0.0',
    'category': 'Dental',
    'summary': 'Outbound dental lab order management — crowns, bridges, aligners and other lab work with status tracking.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_hospital',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/lab_order_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Lab Work Orders\n======================\nManage the full lifecycle of dental laboratory work from within Odoo.\n\nFeatures\n--------\n- Lab order creation from treatment plan lines (crown, bridge, veneer, aligner, etc.)\n- Lab catalogue with preferred laboratories, pricing and turnaround time\n- Order status workflow: draft → sent to lab → in progress → received → fitted\n- Expected and actual return date tracking with overdue alerts\n- Lab shade and material specification fields\n- Digital impression and reference image attachments\n- Lab cost tracking with profitability impact on treatment\n- Outstanding lab orders dashboard for front desk\n\nIntegrates with Dental Treatment Plans and Dental Charting Pro.\n',
    'price': 0,
    'currency': 'USD',
}
