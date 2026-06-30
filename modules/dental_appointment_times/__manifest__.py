{
    'name': 'Dental Appointment Times',
    'version': '18.0.1.0.0',
    'category': 'Medical',
    'summary': 'Adds proper start and end time fields to dental appointments with calendar drag-and-drop support.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'dental_patient_flow',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/appointment_times_views.xml',
    ],
    'assets': {'web.assets_backend': ['dental_appointment_times/static/src/xml/float_time_dropdown.xml', 'dental_appointment_times/static/src/js/float_time_dropdown.js']},
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'description': 'Dental Appointment Times\n========================\nExtends the core dental appointment model with precise scheduling fields.\n\nFeatures\n--------\n- Start time and end time fields with duration auto-calculation\n- Calendar view with drag-and-drop reschedule and resize\n- Overlap validation — warns when a dentist is double-booked\n- Default duration per treatment type\n- Colour coding by appointment status on the calendar\n\nCompatible with the Dental Patient Flow Board and Online Booking modules.\n',
    'price': 0,
    'currency': 'USD',
}
