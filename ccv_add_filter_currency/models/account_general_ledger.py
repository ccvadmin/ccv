# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
from odoo import models, fields
from collections import defaultdict
import logging
_logger = logging.getLogger(__name__)

class GeneralLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals):
        lines = []
        date_from = fields.Date.from_string(options['date']['date_from'])
        company_currency = self.env.company.currency_id

        totals_by_column_group = defaultdict(lambda: {'debit': 0, 'credit': 0, 'balance': 0, 'foreign_balance': 0})
        for account, column_group_results in self._query_values(report, options):
            eval_dict = {}
            has_lines = False
            for column_group_key, results in column_group_results.items():
                account_sum = results.get('sum', {})
                account_un_earn = results.get('unaffected_earnings', {})

                account_debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
                account_credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
                account_balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

                eval_dict[column_group_key] = {
                    'amount_currency': account_sum.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
                    'debit': account_debit,
                    'credit': account_credit,
                    'balance': account_balance,
                    'foreign_balance': account_balance,
                }

                max_date = account_sum.get('max_date')
                has_lines = has_lines or (max_date and max_date >= date_from)

                totals_by_column_group[column_group_key]['debit'] += account_debit
                totals_by_column_group[column_group_key]['credit'] += account_credit
                totals_by_column_group[column_group_key]['balance'] += account_balance
                totals_by_column_group[column_group_key]['foreign_balance'] += account_balance

            lines.append(self._get_account_title_line(report, options, account, has_lines, eval_dict))

        # Report total line.
        for totals in totals_by_column_group.values():
            totals['balance'] = company_currency.round(totals['balance'])
            totals['foreign_balance'] = company_currency.round(totals['foreign_balance'])

        # Tax Declaration lines.
        journal_options = report._get_options_journals(options)
        if len(options['column_groups']) == 1 and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            lines += self._tax_declaration_lines(report, options, journal_options[0]['type'])
        # Total line
        lines.append(self._get_total_line(report, options, totals_by_column_group))

        return [(0, line) for line in lines]

    def _get_aml_line(self, report, parent_line_id, options, eval_dict, init_bal_by_col_group):
        res = super(GeneralLedgerCustomHandler, self)._get_aml_line(report, parent_line_id, options, eval_dict, init_bal_by_col_group)
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