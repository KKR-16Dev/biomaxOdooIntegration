{
    'name': 'Vehicle Certificate Reminder',
    'version': '19.0.1',
    'category': 'Fleet',
    'summary': 'Automatic reminders for vehicle certificate expiry',
    'author': 'KKR',
    'website': 'https://www.KKRGroups.com',
    'depends': ['fleet', 'mail'],
    'data': [
        'views/fleet_vehicle_views.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}