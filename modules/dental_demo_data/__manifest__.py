{
    'name': 'Dental Demo Dataset (Sales Demos)',
    'version': '18.0.1.1.0',
    'category': 'Healthcare/Dental',
    'summary': 'Realistic Arabic demo dataset — patients, dentists, treatments, charts and appointments — ideal for sales demos.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_hospital',
        'dental_charting_pro',
        'dental_ux_fixes',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'demo': [
        'demo/demo_dentists.xml',
        'demo/demo_treatments.xml',
        'demo/demo_patients.xml',
        'demo/demo_appointments.xml',
    ],
    'description': 'Dental Demo Dataset\n===================\nLoad a rich, realistic demo environment for sales demonstrations and training.\n\nIncluded Data\n-------------\n- 30 patient records with Arabic names, demographics and medical history\n- 5 dentist profiles across two branches\n- 50+ appointment records in various statuses\n- Charted teeth conditions across sample patients\n- Sample treatment plans (single and multi-session)\n- Insurance claims in draft, submitted and approved states\n- Lab orders with results\n- SOAP note samples\n- Consumable stock levels\n\nUsage\n-----\nInstall on a clean Odoo instance before demonstrating the Afia Clinic suite.\nUninstall to remove all demo records without affecting configuration.\n',
    'price': 0,
    'currency': 'USD',
}
