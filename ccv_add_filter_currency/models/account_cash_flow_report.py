# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import get_lang

import logging
_logger = logging.getLogger(__name__)

class CashFlowReportCustomHandler(models.AbstractModel):
    _inherit = 'account.cash.flow.report.handler'

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals):
        # Compute the cash flow report using the direct method: https://www.investopedia.com/terms/d/direct_method.asp
        lines = []

        layout_data = self._get_layout_data()
        report_data = self._get_report_data(report, options, layout_data)

        for layout_line_id, layout_line_data in layout_data.items():
            lines.append((0, self._get_layout_line(report, options, layout_line_id, layout_line_data, report_data)))

            if layout_line_id in report_data and 'aml_groupby_account' in report_data[layout_line_id]:
                for aml_data in report_data[layout_line_id]['aml_groupby_account'].values():
                    lines.append((0, self._get_aml_line(report, options, aml_data)))

        unexplained_difference_line = self._get_unexplained_difference_line(report, options, report_data)

        if unexplained_difference_line:
            lines.append((0, unexplained_difference_line))

        return lines

    def _get_report_data(self, report, options, layout_data):
        res = super(CashFlowReportCustomHandler, self)._get_report_data(report, options, layout_data)
        for key in res.keys():
            balance = res[key].get('balance', False)
            if balance:
                res[key].update({'foreign_balance' : balance})
        return res

    def _get_aml_line(self, report, options, aml_data):
        if aml_data:
            foreign_balance = aml_data.get('balance', 0.0)
            aml_data.update({'foreign_balance': foreign_balance})
        res = super(CashFlowReportCustomHandler, self)._get_aml_line(report, options, aml_data)
        columns = res['columns']
        index_update = []
        index_replace = []

        for count, column_option in enumerate(options['columns']):
            if column_option.get("expression_label") == 'balance':
                index_update.append(count)
            elif column_option.get("expression_label") == 'foreign_balance':
                index_replace.append(count)
                
        cur_column = None
        for column_index, column in enumerate(columns):
            if column_index in index_update:
                cur_column = column

        for column_index in index_replace:
                if cur_column is not None:
                    columns[column_index] = cur_column
        return res