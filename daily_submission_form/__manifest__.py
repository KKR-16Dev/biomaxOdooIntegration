{
    'name': 'Daily Submission Form',
    'version': '1.0.0',
    'category': 'Website',
    'summary': 'Customer daily submission form with location tracking',
    'description': """
        Daily Submission Form Module
        =============================
        - Web-based submission form
        - Auto-capture GPS location
        - Google Maps integration
        - Customer feedback collection
    """,
    'author': 'KKR',
    'website': 'https://www.KKRGroups.com',
    'depends': ['base', 'web', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/daily_submission_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'daily_submission_form/static/src/css/daily_submission.css',
            'daily_submission_form/static/src/js/location_capture.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
