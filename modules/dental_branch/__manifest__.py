{
    'name': 'Dental Multi-Branch',
    'version': '18.0.1.0.1',
    'category': 'Dental',
    'summary': 'Multi-branch and clinic chain management with per-branch configuration, staff assignment and cross-branch reporting.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
    ],
    'data': [
        'views/res_company_branch_views.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Multi-Branch Management\n===============================\nManage a chain of dental clinics from a single Odoo instance.\n\nFeatures\n--------\n- Branch model with address, contact details and operating hours\n- Staff assignment per branch (dentists, reception, lab)\n- Per-branch default currency, tax and invoice template\n- Access control — staff see only their branch data by default\n- Cross-branch manager view — compare KPIs across all branches\n- Branch selector on all clinical and billing forms\n- Branch-level appointment calendar\n\nIntegrates with Dental Analytics for consolidated group reporting.\n',
    'price': 0,
    'currency': 'USD',
}
