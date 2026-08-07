{
    'name': 'Dental Patient Portal',
    'version': '18.0.1.0.1',
    'category': 'Portal',
    'summary': 'Patient self-service portal — view appointments, download invoices, prescriptions and consent documents.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'portal',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Patient Portal\n=====================\nGive patients 24/7 online access to their clinic records through the Odoo portal.\n\nPatient Can View\n----------------\n- Upcoming and past appointments\n- Treatment history and clinical summaries\n- Invoices and payment receipts (downloadable PDF)\n- Active prescriptions\n- Signed consent forms\n- Lab results (where shared by the clinic)\n\nPatient Can Do\n--------------\n- Request an appointment (routed to reception for confirmation)\n- Send a message to the clinic\n- Update contact details\n\nPortal Access\n-------------\nPatients receive a portal invitation email. Login via the standard Odoo portal.\nMulti-language: English and Arabic supported.\n',
    'price': 0,
    'currency': 'USD',
}
