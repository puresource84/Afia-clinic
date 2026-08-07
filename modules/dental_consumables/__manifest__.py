{
    'name': 'Dental Consumables',
    'version': '18.0.1.3.1',
    'category': 'Healthcare/Dental',
    'summary': 'Auto-deduct consumable stock when a dental treatment is completed — composite, anaesthetic, gloves and more.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'stock',
        'clinic_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/treatment_views.xml',
        'views/stock_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Procedure Consumables\n=============================\nConnects dental treatments directly to Odoo inventory so consumables are deducted automatically.\n\nFeatures\n--------\n- Bill of Materials (BOM) per procedure — define which consumables each treatment uses\n- Auto-deduction on treatment completion (anesthetic ampoules, gloves, composite, etc.)\n- Low-stock alert when a consumable drops below the reorder point\n- Consumable cost added to procedure cost for accurate profitability reporting\n- Manual override for exceptional usage\n- Per-branch stock location support\n- Stock movement history linked to the treatment record\n\nRequires Odoo Inventory (stock) and the base afia_dental_core module.\n',
    'price': 0,
    'currency': 'USD',
}
