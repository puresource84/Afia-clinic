{
    'name': 'Dental Perio Charting',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Full periodontal examination chart with 6-point pocket depth, bleeding index, recession and mobility per tooth.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_hospital',
        'clinic_core',
        'dental_soap_notes',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/perio_exam_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Perio Charting\n=====================\nA dedicated periodontal examination module for comprehensive gum health recording.\n\nRecorded Per Tooth (6 points)\n-----------------------------\n- Pocket depth (mm)\n- Bleeding on probing (BOP)\n- Gingival recession\n- Furcation involvement grade\n- Tooth mobility grade\n- Plaque index\n\nFeatures\n--------\n- Numeric grid entry — fast keyboard input optimised for clinical charting\n- Automatic BOP percentage calculation\n- Comparison view between two examination dates (to track treatment progress)\n- Perio summary report (PDF) for patient communication\n- Colour-coded severity indicators (healthy / moderate / severe)\n- Links to SOAP notes and treatment plan\n\nIntegrates with Dental Charting Pro.\n',
    'price': 0,
    'currency': 'USD',
}
