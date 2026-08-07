{
    'name': 'Dental Imaging',
    'version': '18.0.1.2.0',
    'category': 'Healthcare/Dental',
    'summary': 'Per-tooth and per-visit photo and X-ray gallery with attachment-based storage and clinical annotations.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'dental_charting_pro',
        'dental_ux_fixes',
    ],
    'data': [
        'views/imaging_tooth_views.xml',
        'views/imaging_appointment_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Imaging\n==============\nOrganise and view patient dental images directly within Odoo.\n\nFeatures\n--------\n- Image gallery per patient, organised by tooth number and visit date\n- Upload X-rays, intraoral photos, panoramic and CBCT scan images\n- Annotate images with clinical notes\n- Link images to specific teeth on the odontogram\n- Before/after comparison view\n- PDF imaging report with selected images\n- Access control — only clinical roles can view imaging records\n- Supports JPEG, PNG, TIFF and PDF formats (no DICOM in this version)\n\nIntegrates with Dental Charting Pro for tooth-linked image display.\n',
    'price': 0,
    'currency': 'USD',
}