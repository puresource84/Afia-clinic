{
    'name': 'Dental Booking Slots',
    'version': '18.0.1.0.2',
    'category': 'Healthcare/Dental',
    'summary': 'Real-time slot-based online booking computed from dentist shifts — patients book exact appointment times.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_portal_booking',
        'afia_dental_core',
    ],
    'data': [
        'views/templates.xml',
        'views/appointment_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': "Dental Online Booking — Time Slots\n====================================\nUpgrades the basic booking page with a live slot grid computed from each dentist's working hours.\n\nFeatures\n--------\n- Slot grid generated from shift templates and chair availability\n- Real-time availability — booked slots hidden instantly\n- Service selection before slot selection (filtering by dentist competency)\n- Patient confirmation email with calendar attachment (.ics)\n- Buffer time between slots (configurable per dentist)\n- Slot hold on form open — released after 5 minutes if not confirmed\n- Works alongside Dental Online Booking (dental_portal_booking)\n",
    'price': 0,
    'currency': 'USD',
}
