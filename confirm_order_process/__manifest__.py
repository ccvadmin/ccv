# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Confirm Order Process',
    'version': '1.3',
    'category': 'Sales',
    'description': """Confirm Order Process""",
    'depends': [
        'base','website','sale', 'mrp',
    ],
    'data': [
        'sercurity/ir.model.access.csv',
        'data/system_parameter.xml',
        'data/cron.xml',
        'views/qweb/confirm_delivery.xml',
        'views/qweb/notify.xml',
        'views/qweb/file_upload_template.xml',
        "views/qweb/confirm_order.xml",
        'views/qweb/file_upload_template.xml',
        "views/base_view.xml",
        "views/mrp_production.xml",
        "views/sale_order.xml",
        "views/user_ip_history_view.xml",
    ],
    'installable': True,
    'license': 'LGPL-3',
}
