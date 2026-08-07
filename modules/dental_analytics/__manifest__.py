{
    'name': 'Dental Analytics & KPIs',
    'version': '18.0.1.0.0',
    'category': 'Dental',
    'summary': 'Dental-specific KPI dashboards: chair utilisation, revenue per dentist, no-show rate and patient retention.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': [
        'afia_dental_core',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/dental_analytics_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'description': 'Dental Analytics & KPIs\n========================\nPurpose-built analytics for dental practice managers.\n\nDashboards\n----------\n- Chair Utilisation — booked vs available hours per chair per day/week/month\n- Revenue per Dentist — invoiced and collected, with trend lines\n- No-Show & Cancellation Rate — by dentist, branch and period\n- Patient Retention — new vs returning patient ratio\n- Treatment Acceptance Rate — presented vs accepted treatment plans\n\nAll dashboards support branch and date-range filtering.\nExport to PDF and Excel for management reporting.\n',
    'price': 0,
    'currency': 'USD',
}
