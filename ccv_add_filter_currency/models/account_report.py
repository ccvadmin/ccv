from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

NOT_APPLY_KEYS = ['foreign_balance']

class AccountReport(models.Model):
    _inherit = 'account.report'

    ##################
    # Filter tiền tệ #
    ##################

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

        company_currency = self.env.company.currency_id
        currency = company_currency
        rate = 1
        if options.get('currency_options', False):
            currency_id = [currency['id'] for currency in options['currency_options'] if currency['selected']]
            if len(currency_id) > 0:
                currency = self.env['res.currency'].browse(int(currency_id[0]))
                if currency.id != company_currency.id:
                    rate = currency.rate

        rate_nt = 1
        if options.get('currency_nt_options', False):
            currency_nt_id = [currency['id'] for currency in options['currency_nt_options'] if currency['selected']]
            currency_nt = company_currency
            if len(currency_nt_id) > 0:
                currency_nt = self.env['res.currency'].browse(int(currency_nt_id[0]))
                if currency_nt.id != company_currency.id:
                    rate_nt = currency_nt.rate

        index_update = []
        index_update1 = []
        for count, column_option in enumerate(options['columns']):
            if column_option.get("figure_type") == "monetary" and column_option.get("expression_label") not in NOT_APPLY_KEYS:
                index_update.append(count)
            elif column_option.get("figure_type") == "monetary" and column_option.get("expression_label") in NOT_APPLY_KEYS:
                index_update1.append(count)
        if index_update or index_update1:
            for line in lines:
                columns = line['columns']
                updated_columns = []
                for column_index, column in enumerate(columns):
                    new_obj = {'name': column.get('name', ''), 'no_format': column.get('no_format', '0'), 'class': column.get('class', '')}
                    if column_index in index_update and column.get('no_format') is not None:
                        no_format_value = float(new_obj['no_format'] * rate) if isinstance(new_obj['no_format'], (int, float)) else 0.0
                        name = currency.format(no_format_value)
                        new_obj.update({
                            "name": name,
                            "no_format": no_format_value
                        })
                        updated_columns.append(new_obj)
                    elif column_index in index_update1 and column.get('no_format') is not None:
                        no_format_value = float(new_obj['no_format'] * rate_nt) if isinstance(new_obj['no_format'], (int, float)) else 0.0
                        name = currency_nt.format(no_format_value)
                        new_obj.update({
                            "name": name,
                            "no_format": no_format_value
                        })
                        updated_columns.append(new_obj)
                    else:
                        updated_columns.append(column)
                line['columns'] = updated_columns

        return lines


    #########################
    # Filter số dư ngoại tệ #
    #########################

    filter_currency_nt = fields.Boolean(
        string="Currencies NT",
        compute=lambda x: x._compute_report_option_filter('filter_currency_nt', True),
        readonly=False,
        store=True,
        depends=['root_report_id'],
    )

    def _init_options_currency_nt(self, options, previous_options=None):
        if not self.filter_currency_nt:
            return
        currencies = self.env['res.currency'].search([])
        currency_nt_options = [{'id': 2, 'name': "USD", 'selected': True}]
        currency_nt_options += [{'id': currency.id, 'name': currency.name, 'selected': False} for currency in currencies if currency.id != 2]
        options['currency_nt_options'] = currency_nt_options

        if previous_options and previous_options.get('currency_nt_options'):
            previously_selected_ids = {x['id'] for x in previous_options['currency_nt_options'] if x.get('selected')}
            for opt in options['currency_nt_options']:
                opt['selected'] = opt['id'] in previously_selected_ids