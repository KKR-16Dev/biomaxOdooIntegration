{
    'name': 'Night Shift Attendance Filter',
    'version': '18.0.1.0.0',
    'summary': 'Dynamic night shift filter 6PM-3AM IST for hr.attendance',
    'depends': ['hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_attendance_view.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
