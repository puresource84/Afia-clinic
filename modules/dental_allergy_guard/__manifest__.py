{
    'name': 'Dental Allergy Guard',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Hard-stop allergy alerts that block prescribing a drug matching a patient allergy — prevents clinical errors.',
    'description': 'Dental Allergy Guard\n====================\nSafety-critical module that adds a hard block when a clinician attempts to prescribe\nor chart a treatment involving a substance the patient is allergic to.\n\nFeatures\n--------\n- Patient allergy list with severity grading (mild / moderate / severe / life-threatening)\n- Hard-stop validation on prescription and treatment plan lines\n- Pop-up alert with allergy details and override requires Manager confirmation\n- Allergy history log with date recorded and recorded-by user\n- Quick-add allergy from the prescription form\n\nClinical Compliance\n-------------------\nDesigned to support JCI and MOH dental clinic accreditation requirements.\n',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'dental_ux_fixes',
        'clinic_core',
        'dental_charting_pro',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/allergy_substances.xml',
        'views/allergy_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'price': 0,
    'currency': 'USD',
}
