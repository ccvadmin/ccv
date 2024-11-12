# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Bao Cao CCV',
    'version': '1.3',
    'category': 'Accounting',
    'description': """Bao Cao CCV""",
    'depends': [
        'account',
        # 'ccv_sql',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/beta_views.xml',
        'views/report_views.xml',
        'report/bao_cao_ccv_report.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
