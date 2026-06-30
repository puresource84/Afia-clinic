{
    'name': 'Dental Online Booking',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Public online appointment booking page for dental clinics — patients book without logging in.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_hospital',
        'website',
        'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Online Booking\n=====================\nA public-facing appointment request page accessible from your clinic website.\n\nPatient Flow\n------------\n1. Patient visits the booking page (no login required)\n2. Selects service and preferred dentist\n3. Picks available date and time\n4. Enters name, phone and chief complaint\n5. Receives confirmation email with appointment summary\n\nClinic Flow\n-----------\n- New booking appears as a pending appointment for reception to confirm\n- Optional auto-confirm for returning patients\n- Daily booking summary email to the clinic manager\n\nFeatures\n--------\n- Mobile-responsive booking form\n- reCAPTCHA spam protection\n- Bilingual: Arabic and English\n- Embed on any page with a simple URL or iframe\n\nUpgrade with Dental Online Booking — Time Slots for real-time slot availability.\n',
    'price': 0,
    'currency': 'USD',
}
