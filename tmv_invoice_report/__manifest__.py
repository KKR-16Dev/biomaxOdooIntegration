# -*- coding: utf-8 -*-
{
    "name": "TMV Invoice Report",
    "summary": "Custom GST invoice print matching TMV layout",
    "version": "1.5",
    "author": "KKR",
    "website": "https://www.kaviglobal.com",
    "license": "LGPL-3",
    "category": "Accounting/Reporting",
    "depends": ['base', 'account'],
    "data": [
        "report/report_paperformat.xml",
        "report/invoice_tmv_report.xml",
        "views/res_company_views.xml",
    ],
    "assets": {},
    "application": False,
    "installable": True,
}
