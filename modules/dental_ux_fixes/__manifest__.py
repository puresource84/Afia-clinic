{
    'name': 'Clinic UX & Branding',
    'version': '18.0.2.1.8',
    'category': 'Healthcare/Dental',
    'summary': 'Afia Clinic branding, UI polish and UX improvements — refined menus, colour theme and booking-time validation.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'dental_insurance',
        'dental_treatment_plan',
        'dental_consent',
        'dental_lab',
        'dental_sterilization',
        'clinic_core',
        # clinic_core_plus dependency removed 2026-07-15: that module was an
        # abandoned duplicate of clinic_core (same 4 settings fields, never
        # truly extended anything) and is being retired. See menu_dedupe.xml
        # and menu_configure_groups.xml in this module for the corresponding
        # cleanup of its now-removed menu entry.
        'stock',
        'dental_portal_booking',
        'dental_reminders_telegram',
        'dental_telegram_templates',
        'dental_analytics',
        'dental_appointment_times',
        'dental_patient_flow',
        'dental_soap_notes',
        'dental_perio_charting',
        'custom_dental_menu',
        # 2026-08: added — clinic_stock_menu.xml references
        # dental_consumables.menu_clinic_stock by external ID, but this
        # module was missing from depends. Worked by coincidence in prior
        # test databases where dental_consumables was already installed
        # from an earlier session; a genuine from-scratch install exposes
        # the missing dependency as a ParseError (uninstalled module).
        'dental_consumables',
    ],
    'data': [
        'security/ir.model.access.csv',
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
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'description': 'Afia Clinic — UX & Branding\n============================\nVisual polish and user experience improvements across the entire Afia Clinic suite.\n\nIncluded\n--------\n- Afia Clinic colour theme applied to the backend (primary blue #1a73a7)\n- Clinic logo on login page and main menu\n- Refined navigation menus — removed redundant items, logical grouping\n- Booking time validation — prevents scheduling outside working hours\n- Form view improvements: field ordering, label clarity, help tooltips\n- Arabic RTL layout fixes across clinical forms\n- Mobile-responsive adjustments for tablet use in the clinic\n- Loading skeleton screens to reduce perceived wait time\n\nNo configuration required — improvements apply automatically on installation.\n',
    'price': 0,
    'currency': 'USD',
}
