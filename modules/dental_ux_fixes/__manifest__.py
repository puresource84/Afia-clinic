# -*- coding: utf-8 -*-
{'name': 'Clinic UX & Branding',
 'version': '18.0.2.2.7',
 'category': 'Healthcare/Dental',
 'summary': 'Afia Clinic branding, UI polish and UX improvements — refined menus, colour theme and '
            'booking-time validation.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'depends': ['afia_dental_core',
             'calendar',
             'dental_insurance',
             'dental_treatment_plan',
             'dental_consent',
             'dental_lab',
             'dental_sterilization',
             'stock',
             'dental_portal',
             'dental_reminders',
             'dental_analytics',
             'dental_patient_flow',
             'dental_soap_notes',
             'dental_charting',
             'afia_menu',
             'dental_consumables'],
 'data': ['security/ir.model.access.csv',
          'views/patient_action_fix.xml',
          'views/res_partner_views.xml',
          'views/dental_claim_form_fix.xml',
          'views/dental_appointment_view_fix.xml',
          'views/chatter_fixes.xml',
          'views/menu_dedupe.xml',
          'views/menu_quick_actions.xml',
          'views/menu_configure_groups.xml',
          'wizards/clinic_user_wizard_views.xml',
          'views/dental_prescription_rtl_fix.xml',
          'views/clinic_stock_menu.xml',
          'views/front_desk_reporting.xml',
          'views/menu_restructure.xml',
          'views/res_users_staff_views.xml',
          'views/menu_staff.xml',
          'views/res_partner_calendar_meetings_fix.xml'],
 'assets': {'web.assets_backend': ['dental_ux_fixes/static/src/patient_form/patient_details.scss']},
 'images': ['static/description/icon.png'],
 'installable': True,
 'application': False,
 'description': 'Afia Clinic — UX & Branding\n'
                '============================\n'
                'Visual polish and user experience improvements across the entire Afia Clinic '
                'suite.\n'
                '\n'
                'Included\n'
                '--------\n'
                '- Afia Clinic colour theme applied to the backend (primary blue #1a73a7)\n'
                '- Clinic logo on login page and main menu\n'
                '- Refined navigation menus — removed redundant items, logical grouping\n'
                '- Booking time validation — prevents scheduling outside working hours\n'
                '- Form view improvements: field ordering, label clarity, help tooltips\n'
                '- Arabic RTL layout fixes across clinical forms\n'
                '- Mobile-responsive adjustments for tablet use in the clinic\n'
                '- Loading skeleton screens to reduce perceived wait time\n'
                '\n'
                'No configuration required — improvements apply automatically on installation.\n',
 'price': 0,
 'currency': 'USD'}
