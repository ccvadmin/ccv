from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class AccountReport(models.Model):
    _inherit = 'account.report'

    filter_currency = fields.Boolean(
        string="Currencies",
        compute=lambda x: x._compute_report_option_filter('filter_currency', True),
        readonly=False,
        store=True,
        depends=['root_report_id'],
    )

    def _init_options_currency(self, options, previous_options=None):
        if not self.filter_currency:
            return
            
        # Fetch only active currencies
        currencies = self.env['res.currency'].search([])
        options['currency_options'] = [
            {'id': currency.id, 'name': currency.name, 'selected': False} for currency in currencies
        ]

        if previous_options and previous_options.get('currency_options'):
            previously_selected_ids = {x['id'] for x in previous_options['currency_options'] if x.get('selected')}
            for opt in options['currency_options']:
                opt['selected'] = opt['id'] in previously_selected_ids

    def _get_lines(self, options, all_column_groups_expression_totals=None):
        self.ensure_one()
        lines = super(AccountReport, self)._get_lines(options, all_column_groups_expression_totals)

        currency_id = [currency['id'] for currency in options['currency_options'] if currency['selected']]
        
        if len(currency_id) > 0:
            company_currency = self.env.company.currency_id
            currency = self.env['res.currency'].browse(int(currency_id[0]))
            if currency.id != company_currency.id:
                index_update = []
                for count, column_option in enumerate(options['columns']):
                    if column_option.get("figure_type") == "monetary":
                        index_update.append(count)
                for line in lines:
                    for column_index, column in enumerate(line['columns']):
                        if column_index in index_update and column.get('no_format') is not None:
                            no_format_value = float(column['no_format'] * currency.rate) if isinstance(column['no_format'], (int, float)) else 0.0
                            column['name'] = currency.format(no_format_value)
                            column['no_format'] = no_format_value
                            
        return lines

