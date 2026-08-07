{
    'name': 'Dental Case Acceptance',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Present treatment plans to patients on a tablet and capture e-signatures — improves case acceptance rates.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_treatment_plan',
        'dental_consent',
        'dental_analytics',
    ],
    'data': [
        'views/treatment_plan_acceptance_views.xml',
        'views/consent_signature_views.xml',
        'report/treatment_plan_proposal_report.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Case Acceptance & E-Signature\n=====================================\nStreamlines the treatment plan presentation and patient sign-off process.\n\nFeatures\n--------\n- Patient-facing treatment plan presentation view (optimised for tablet)\n- Line-by-line cost breakdown with procedure descriptions\n- Capture patient e-signature on screen using touch or stylus\n- Signed PDF generated automatically and attached to the treatment plan\n- Partial acceptance — patient can accept selected lines and defer others\n- Acceptance rate tracking per dentist and treatment type\n- Pending signature reminder after 24 hours\n\nIntegrates with Dental Treatment Plans and Dental Consent Forms.\n',
    'price': 0,
    'currency': 'USD',
}
