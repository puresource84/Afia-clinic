{
    # ITCS-internal module: manages self-hosted client license/AMC expiry,
    # renewal codes, and Telegram alerts to ITCS. Deliberately kept as its
    # own standalone module (depends only on 'base') so it never touches or
    # depends on any clinical module — it can be added, updated, or removed
    # from any clinic instance without affecting appointments, patients,
    # billing, or any other clinical functionality.
    #
    # Design principles (2026-07-17, per Manhel's direction):
    # - Never hard-block a clinic's access to patient data. Past the grace
    #   period, the system goes read-only (view/export still allowed),
    #   never a full lockout. See models/itcs_license.py for details.
    # - No anti-uninstall locks, no gating of what modules can be installed.
    #   The Bytekol SaaS kit removed earlier this session did both of those
    #   things and it was the wrong model — this module must never repeat it.
    # - Clinic staff (including the clinic's own "admin" user) must never
    #   see this module's menu, model, or data. Only the group defined in
    #   security/security.xml can.
    'name': 'ITCS License Manager',
    'version': '18.0.1.0.0',
    'category': 'Hidden/Tools',
    'summary': 'ITCS-internal: self-hosted license/AMC expiry tracking, renewal codes, Telegram alerts.',
    'author': 'ITCS (IT Corner Solutions)',
    'website': 'https://www.itcornersolutions.net/',
    'license': 'OPL-1',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/itcs_license_views.xml',
        'views/apply_code_wizard_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'description': (
        'ITCS License Manager\n=====================\n'
        'Internal tool for ITCS to track each self-hosted Afia Clinic '
        "instance's license/AMC expiry, apply signed renewal codes, and "
        'receive Telegram alerts before/after expiry. Not visible to '
        'clinic staff. Never blocks clinical data access — read-only mode '
        'only, past a grace period.\n'
    ),
}
