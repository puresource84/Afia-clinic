{
    'name': 'Dental Clinical Permissions',
    'version': '18.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Role-based access matrix — clinical records are locked to clinical roles; billing locked to admin roles.',
    'description': 'Dental Clinical Permissions\n===========================\nEnforces a strict role matrix across the Afia Clinic suite.\n\nRoles\n-----\n- Clinic Manager — full access to all records and configuration\n- Dentist / Clinician — read-write on clinical records; read-only on billing\n- Hygienist — clinical notes and charting only; no prescriptions\n- Receptionist — appointments and patient demographics; no clinical records\n- Lab Technician — lab orders only\n- Billing Admin — invoices, insurance claims, payments; no clinical records\n\nFeatures\n--------\n- Record rules applied at the model level (not just menu hiding)\n- Audit log of permission changes\n- Conflict checker — warns if a user has conflicting roles\n\nRequires clinic_core for base group definitions.\n',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'clinic_core',
        'dental_hospital',
        'dental_charting_pro',
        'dental_treatment_plan',
        'dental_consent',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/access_overrides.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'price': 0,
    'currency': 'USD',
}
