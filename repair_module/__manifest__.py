# -*- coding: utf-8 -*-
{
    'name': "repair_module",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'sale',
        'report_xlsx',
        'mail',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/repair_serial.xml',
        'data/repair_cron.xml',
        'data/email_template.xml',
        'views/views.xml',
        'views/repair_account.xml',
        'views/templates.xml',
        'views/setting.xml',
        'reports/repair_excel_report.xml',
        'reports/repair_report.xml',
        'reports/repair_reporting.xml',
        'reports/repair_invoice_report.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
