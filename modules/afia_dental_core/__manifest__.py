{
    'name': 'Afia Dental Clinic',
    'version': '18.0.2.0.0',
    'category': 'Healthcare',
    'summary': 'Dental clinic core: patients, appointments, dentists, treatments, prescriptions and billing.',
    'description': """
Afia Dental Clinic — Core
==========================
Clean-room rewrite (2026-08) of the foundation module for the Afia Clinic
suite. Provides the shared data model every other Afia Dental Clinic
module builds on: patients, appointments, dentists, treatments,
prescriptions and billing.

Highlights over the previous core
----------------------------------
- Appointments are backed by Odoo's native Calendar app (calendar.event) —
  real start/end datetimes, dentist capacity awareness, ICS export, and a
  normal calendar view, instead of a bespoke date-only field.
- No more denormalized patient snapshot data copied onto every
  appointment — clinical details are read live from the patient record.
- Native multi-company support (company_id + record rules) instead of
  bolting it on later.
- Doctor accounts are created through a deliberate, auditable invite flow
  with a real password reset link — not a silent, passwordless user
  creation on every employee record.
- Consistent chatter/activity tracking across all clinical models.

This module is the required dependency for every other Afia Dental
Clinic module.
""",
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'base',
        'hr',
        'account',
        'sale',
        'product',
        'web',
        'stock',
        'calendar',
        'mail',
        'resource',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/sequences.xml',
        'data/dental_specialist_data.xml',
        'data/treatment_category_data.xml',
        'data/dental_treatment_data.xml',
        'data/dental_time_shift_data.xml',
        'data/medicine_frequency_data.xml',
        'views/res_partner_views.xml',
        'views/hr_employee_views.xml',
        'views/dental_specialist_views.xml',
        'views/treatment_category_views.xml',
        'views/dental_treatment_views.xml',
        'views/dental_time_shift_views.xml',
        'views/dental_appointment_views.xml',
        'views/dental_prescription_views.xml',
        'views/dental_medicine_views.xml',
        'views/medical_questions_views.xml',
        'views/teeth_chart_views.xml',
        'views/account_payment_views.xml',
        'views/menus.xml',
        'report/dental_prescription_report.xml',
        'report/dental_prescription_templates.xml',
        'wizard/doctor_invite_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'company': 'ITCS (IT Corner Solutions)',
    'maintainer': 'ITCS (IT Corner Solutions)',
    'support': 'support@itcornersolutions.net',
    'price': 599,
    'currency': 'USD',
}
