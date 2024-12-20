# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Confirm Order Process',
    'version': '1.3',
    'category': 'Sales/Confirm Order',
    'description': """Confirm Order Process""",
    'depends': [
        'base','website','sale_management', 'mrp', 'sms', 'contacts', 'base_geolocalize',
    ],
    'data': [
        'sercurity/groups.xml',
        'sercurity/ir.model.access.csv',
        'data/system_parameter.xml',
        'data/cron.xml',
        'views/qweb/confirm_delivery.xml',
        'views/qweb/map_view.xml',
        'views/qweb/notify.xml',
        'views/qweb/file_upload_template.xml',
        "views/qweb/confirm_order.xml",
        'views/qweb/file_upload_template.xml',
        "views/mrp_production.xml",
        "views/sale_order.xml",
        "views/user_ip_history_view.xml",
        "views/order_link.xml",
        "views/otp_verification.xml",
        "views/sales_order_location.xml",
        "views/tracking_order_config.xml",
        "views/menu.xml",
    ],
    'installable': True,
    'license': 'LGPL-3',
}
