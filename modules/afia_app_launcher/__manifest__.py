# -*- coding: utf-8 -*-
{'name': 'Afia App Launcher',
 'version': '18.0.1.0.4',
 'category': 'Dental/Afia',
 'summary': 'Enterprise-style home screen with role-filtered app tiles, live search and '
            'drag-and-drop personalisation.',
 'author': 'ITCS (IT Corner Solutions)',
 'website': 'https://www.itcornersolutions.net/',
 'license': 'OPL-1',
 'depends': ['web', 'afia_dental_core'],
 'data': ['security/ir.model.access.csv',
          'views/app_launcher_action.xml',
          'views/afia_launcher_branding_views.xml'],
 'assets': {'web.assets_backend': ['afia_app_launcher/static/src/app_launcher/app_launcher.js',
                                   'afia_app_launcher/static/src/app_launcher/app_launcher.xml',
                                   'afia_app_launcher/static/src/app_launcher/app_launcher.scss',
                                   'afia_app_launcher/static/src/navbar_patch/navbar_patch.js']},
 'images': ['static/description/icon.png'],
 'installable': True,
 'auto_install': False,
 'application': False,
 'post_init_hook': 'post_init_hook',
 'description': 'Afia App Launcher\n'
                '=================\n'
                'Replace the default Odoo home menu with a branded, role-aware launcher designed '
                'for clinic staff.\n'
                '\n'
                'Features\n'
                '--------\n'
                '- Configurable tile grid — each tile maps to an Odoo app or URL\n'
                '- Role filtering — reception sees scheduling tiles; clinicians see clinical '
                'tiles\n'
                '- Live search across all visible apps\n'
                '- Drag-and-drop tile ordering per user\n'
                '- Clinic branding: logo, background colour, welcome message\n'
                '- Works on desktop and tablet (responsive)\n'
                '\n'
                'Installation\n'
                '------------\n'
                'Install the module and configure tiles under Configuration → App Launcher.\n'}
