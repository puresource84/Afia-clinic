{
    'name': 'Dental Demo Dataset',
    'version': '18.0.1.1.0',
    'category': 'Healthcare/Dental',
    'summary': 'Realistic Arabic demo dataset — patients, dentists, treatments, charts and appointments — ideal for sales demos.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
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
    'description': 'Dental Demo Dataset\n===================\nLoad a rich, realistic demo environment for sales demonstrations and training.\nNOT for production/customer clinic databases — seeds fake Arabic patient records.\n\nIncluded Data\n-------------\n- 30 patient records with Arabic names, demographics and medical history\n- 5 dentist profiles across two branches\n- 50+ appointment records in various statuses\n- Charted teeth conditions across sample patients\n- Sample treatment plans (single and multi-session)\n- Insurance claims in draft, submitted and approved states\n- Lab orders with results\n- SOAP note samples\n- Consumable stock levels\n\nInstallation\n------------\nThis module ships its records under Odoo\'s "demo" data mechanism, not\n"data" - they only load if demo data is enabled for the target database.\n\n1. Create a NEW, non-production database. In the Odoo database manager\n   (/web/database/manager), make sure the "Demo data" checkbox is\n   CHECKED when creating it.\n2. Go to Apps, remove the "Apps" filter, search "Dental Demo Dataset",\n   click Install. Dependencies (afia_dental_core, dental_charting_pro,\n   dental_ux_fixes) install automatically if missing.\n3. Verify under Afia Clinic > Patients - you should see ~30 Arabic\n   patient records. An empty list means demo data was disabled for this\n   database - recreate it with the checkbox enabled.\n\nCommand-line install: pass -i dental_demo_data alongside the core\nmodules, and make sure the config does NOT set without_demo=True and no\n--without-demo flag is passed - either will silently skip all demo\nrecords with no error. Full step-by-step instructions, including the\ncommand-line install workflow, are in this module\'s README.md.\n\nUsage\n-----\nInstall on a clean Odoo instance before demonstrating the Afia Clinic suite.\nUninstall to remove all demo records without affecting configuration.\n',
    'price': 0,
    'currency': 'USD',
}
