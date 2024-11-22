import logging

from collections import defaultdict
from odoo import models, fields

_logger = logging.getLogger(__name__)

KEYS = ['debit', 'credit', 'balance', 'foreign_balance']

class PartnerLedger(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _build_partner_lines(self, report, options, level_shift=0):
        lines = []

        totals_by_column_group = {
            column_group_key: { total: 0.0 for total in KEYS }
            for column_group_key in options['column_groups']
        }

        for partner, results in self._query_partners(options):
            partner_values = defaultdict(dict)

            for column_group_key in options['column_groups']:
                partner_sum = results.get(column_group_key, {})
                for key in KEYS:
                    partner_values[column_group_key][key] = partner_sum.get(key, 0.0)
                    totals_by_column_group[column_group_key][key] += partner_values[column_group_key][key]
            lines.append(self._get_report_line_partners(options, partner, partner_values, level_shift=level_shift))
        return lines, totals_by_column_group

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=0):
        if aml_query_result:
            foreign_balance = aml_query_result.get('balance', 0.0)
            aml_query_result.update({'foreign_balance': foreign_balance})
        
        res = super(PartnerLedger, self)._get_report_line_move_line(options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift)
        columns = res['columns']
        if aml_query_result:
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

    def _query_partners(self, options):
        res = super(PartnerLedger, self)._query_partners(options)
        for partner, results in res:
            for column_group_key in options['column_groups']:
                partner_sum = results.get(column_group_key, {})
                partner_sum['foreign_balance'] = partner_sum.get('balance', 0.0)
        return res

