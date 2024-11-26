from odoo import models, fields, api, _
import logging
import datetime

_logger = logging.getLogger(__name__)

NOT_APPLY_KEYS = ['foreign_balance']
GET_LAST_VALUE_KEYS = ['balance']
GET_LAST_VALUE_NT_KEYS = ['foreign_balance']

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

    def _identify_currency_indices(self, options):
        monetary_index, last_val_index, last_val_nt_index = [], [], []
        index_update, index_update1, index_update2 = [], [], []
        for count, column_option in enumerate(options["columns"]):
            if column_option.get("figure_type") == "monetary":
                monetary_index.append(count)
                if column_option.get("expression_label") in GET_LAST_VALUE_KEYS:
                    last_val_index.append(count)
                elif column_option.get("expression_label") in GET_LAST_VALUE_NT_KEYS:
                    last_val_nt_index.append(count)
                if column_option.get("expression_label") in ['amount_currency']:
                    index_update2.append(count)
                elif column_option.get("expression_label") not in NOT_APPLY_KEYS:
                    index_update.append(count)
                elif column_option.get("expression_label") in NOT_APPLY_KEYS:
                    index_update1.append(count)
        return monetary_index, last_val_index, last_val_nt_index, index_update, index_update1, index_update2

    def _get_selected_currency(self, options, company_currency, currency_env):
        currency = company_currency
        if options.get('currency_options', False):
            currency_id = [currency['id'] for currency in options['currency_options'] if currency['selected']]
            if len(currency_id) > 0:
                currency = currency_env.browse(int(currency_id[0]))

        currency_nt = company_currency
        if options.get('currency_nt_options', False):
            currency_nt_id = [currency['id'] for currency in options['currency_nt_options'] if currency['selected']]
            if len(currency_nt_id) > 0:
                currency_nt = currency_env.browse(int(currency_nt_id[0]))

        return currency, currency_nt

    def _apply_conversion(self, column_obj, rate, currency, column):
        no_format_value = float(column['no_format'] * rate) if isinstance(column['no_format'], (int, float)) else 0.0
        column_obj.update({
            "name": currency.format(no_format_value),
            "no_format": no_format_value
        })
        return column_obj
    
    def _apply_conversion_force(self, column_obj, currency, no_format_value):
        column_obj.update({
            "name": currency.format(no_format_value),
            "no_format": no_format_value
        })
        return column_obj

    def is_date(self, value):
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, str):
            try:
                return datetime.datetime.strptime(value, "%d/%m/%Y").date()
            except ValueError:
                return fields.Date.context_today(self)
        return fields.Date.context_today(self)

    def compute_rate_line(self, currency, line_name):
        cur_date = self.is_date(line_name)
        company = self.env.company
        currency_rates = currency._get_rates(company, cur_date)
        last_rate = self.env['res.currency.rate'].sudo()._get_last_rates_for_companies(company)
        return (currency_rates.get(currency.id) or 1.0) / last_rate[company]

    def _get_lines(self, options, all_column_groups_expression_totals=None):
        self.ensure_one()
        lines = super(AccountReport, self)._get_lines(options, all_column_groups_expression_totals)
        currency_env = self.env['res.currency']
        currency_env = self.env['res.currency']
        monetary_index, last_val_index, last_val_nt_index, index_update, index_update1, index_update2 = self._identify_currency_indices(options)

        if (index_update or index_update1):
            # Xử lý move line
            for line in lines:
                id = line.get("id", "")
                name = line.get("name", "")
                columns = line['columns']

                is_main_line = id == 'total~~'
                is_sub_line = 'total~~' in id and id != 'total~~'

                has_parent = line.get("parent_id", False)
                has_monetary = any([True for index_monetary in monetary_index if columns[index_monetary].get('no_format', None) is not None])

                if not has_monetary or not has_parent or is_sub_line or is_main_line:
                    continue
                
                updated_columns = []
                company_currency = self.env.company.currency_id
                currency, currency_nt = self._get_selected_currency(options, company_currency, currency_env)

                rate = self.compute_rate_line(currency, name)
                rate_nt = self.compute_rate_line(currency_nt, name)
                for column_index, column in enumerate(columns):
                    column_obj = {'name': column.get('name', ''), 'no_format': column.get('no_format', '0'), 'class': column.get('class', '')}
                    if column_index in index_update and column.get('no_format') is not None and rate != 1:
                        updated_columns.append(self._apply_conversion(column_obj, rate, currency, column))
                    elif column_index in index_update1 and column.get('no_format') is not None and rate_nt != 1:
                        updated_columns.append(self._apply_conversion(column_obj, rate_nt, currency_nt, column))
                    else:
                        updated_columns.append(column_obj)
                line['columns'] = updated_columns

            # Xử lý move line tổng
            for line in lines:
                id = line.get("id", "")
                name = line.get("name", "")
                columns = line['columns']

                is_main_line = id == 'total~~'
                is_sub_line = 'total~~' in id and id != 'total~~'

                parent_id = line.get("parent_id", '')
                has_parent = line.get("parent_id", False)
                has_monetary = any([True for index_monetary in monetary_index if columns[index_monetary].get('no_format', None) is not None])

                if not has_monetary or not has_parent or not is_sub_line or is_main_line:
                    continue
                
                updated_columns = []
                company_currency = self.env.company.currency_id
                currency, currency_nt = self._get_selected_currency(options, company_currency, currency_env)

                filter_line = [x for x in lines if x.get("parent_id", '') == parent_id and x['id'] != id]
                if not filter_line:
                    rate = self.compute_rate_line(currency, name)
                    rate_nt = self.compute_rate_line(currency_nt, name)
                    for column_index, column in enumerate(columns):
                        column_obj = {'name': column.get('name', ''), 'no_format': column.get('no_format', '0'), 'class': column.get('class', '')}
                        if column_index in index_update and column.get('no_format') is not None and rate != 1:
                            updated_columns.append(self._apply_conversion(column_obj, rate, currency, column))
                        elif column_index in index_update1 and column.get('no_format') is not None and rate_nt != 1:
                            updated_columns.append(self._apply_conversion(column_obj, rate_nt, currency_nt, column))
                        else:
                            updated_columns.append(column_obj)
                    line['columns'] = updated_columns
                    continue
                list_line = []
                for index in monetary_index:
                    list_line.append(sum([float(x['columns'][index].get('no_format', 0)) if isinstance(x['columns'][index].get('no_format', 0), (int, float)) else 0.0 for x in filter_line]))
                index = 0
                for count, column in enumerate(columns):
                    column_obj = {'name': column.get('name', ''), 'no_format': column.get('no_format', ''), 'class': column.get('class', '')}
                    if count in monetary_index:
                        if count in last_val_index:
                            cur_column = filter_line[-1]['columns'][count]
                            column_obj = self._apply_conversion_force(column_obj, currency, cur_column.get('no_format', ''))
                        elif count in last_val_nt_index:
                            cur_column = filter_line[-1]['columns'][count]
                            column_obj = self._apply_conversion_force(column_obj, currency_nt, cur_column.get('no_format', ''))
                        elif count in index_update:
                            column_obj = self._apply_conversion_force(column_obj, currency, list_line[index])
                        elif count in index_update1:
                            column_obj = self._apply_conversion_force(column_obj, currency_nt, list_line[index])
                        updated_columns.append(column_obj)
                        index += 1
                    else:
                        updated_columns.append(column_obj)
                line['columns'] = updated_columns
            
            # Xử lý line tổng (cạnh tên Partner)
            for line in lines:
                id = line.get("id", "")
                name = line.get("name", "")
                columns = line['columns']

                is_main_line = id == 'total~~'
                is_sub_line = 'total~~' in id and id != 'total~~'

                parent_id = line.get("parent_id", '')
                has_parent = line.get("parent_id", False)
                has_monetary = any([True for index_monetary in monetary_index if columns[index_monetary].get('no_format', None) is not None])

                if not has_monetary or has_parent or is_sub_line or is_main_line:
                    continue
                
                updated_columns = []
                company_currency = self.env.company.currency_id
                currency, currency_nt = self._get_selected_currency(options, company_currency, currency_env)

                filter_line = [x for x in lines if x.get("parent_id", '') == id and "total~~" not in x['id']]
                if not filter_line:
                    rate = self.compute_rate_line(currency, name)
                    rate_nt = self.compute_rate_line(currency_nt, name)
                    for column_index, column in enumerate(columns):
                        column_obj = {'name': column.get('name', ''), 'no_format': column.get('no_format', '0'), 'class': column.get('class', '')}
                        if column_index in index_update and column.get('no_format') is not None and rate != 1:
                            updated_columns.append(self._apply_conversion(column_obj, rate, currency, column))
                        elif column_index in index_update1 and column.get('no_format') is not None and rate_nt != 1:
                            updated_columns.append(self._apply_conversion(column_obj, rate_nt, currency_nt, column))
                        else:
                            updated_columns.append(column_obj)

                    line['columns'] = updated_columns
                    continue
                list_line = []
                for index in monetary_index:
                    list_line.append(sum([float(x['columns'][index].get('no_format', 0)) if isinstance(x['columns'][index].get('no_format', 0), (int, float)) else 0.0 for x in filter_line]))
                index = 0
                for count, column in enumerate(columns):
                    column_obj = {'name': column.get('name', ''), 'no_format': column.get('no_format', ''), 'class': column.get('class', '')}
                    if count in monetary_index:
                        if count in last_val_index:
                            cur_column = filter_line[-1]['columns'][count]
                            column_obj = self._apply_conversion_force(column_obj, currency, cur_column.get('no_format', ''))
                        elif count in last_val_nt_index:
                            cur_column = filter_line[-1]['columns'][count]
                            column_obj = self._apply_conversion_force(column_obj, currency_nt, cur_column.get('no_format', ''))
                        elif count in index_update:
                            column_obj = self._apply_conversion_force(column_obj, currency, list_line[index])
                        elif count in index_update1:
                            column_obj = self._apply_conversion_force(column_obj, currency_nt, list_line[index])
                        updated_columns.append(column_obj)
                        index += 1
                    else:
                        updated_columns.append(column_obj)
                line['columns'] = updated_columns

            # Tổng hết
            for line in lines:
                id = line.get("id", "")
                name = line.get("name", "")
                columns = line['columns']

                is_main_line = id == 'total~~'
                is_sub_line = 'total~~' in id and id != 'total~~'

                parent_id = line.get("parent_id", '')
                has_parent = line.get("parent_id", False)
                has_monetary = any([True for index_monetary in monetary_index if columns[index_monetary].get('no_format', None) is not None])

                if not has_monetary or has_parent or is_sub_line or not is_main_line:
                    continue
                
                updated_columns = []
                company_currency = self.env.company.currency_id
                currency, currency_nt = self._get_selected_currency(options, company_currency, currency_env)

                filter_line = [x for x in lines if "total~~" in x['id'] and x['id'] != "total~~"]
                if not filter_line:
                    filter_line = [x for x in lines if not x.get('parent_id', False) and x['id'] != "total~~"]
                    if not filter_line:
                        continue
                list_line = []
                for index in monetary_index:
                    list_line.append(sum([float(x['columns'][index].get('no_format', 0)) if isinstance(x['columns'][index].get('no_format', 0), (int, float)) else 0.0 for x in filter_line]))
                index = 0
                for count, column in enumerate(columns):
                    column_obj = {'name': column.get('name', ''), 'no_format': column.get('no_format', ''), 'class': column.get('class', '')}
                    if count in monetary_index:
                        if count in index_update or count in last_val_index:
                            column_obj = self._apply_conversion_force(column_obj, currency, list_line[index])
                        elif count in index_update1 or count in last_val_nt_index:
                            column_obj = self._apply_conversion_force(column_obj, currency_nt, list_line[index])
                        updated_columns.append(column_obj)
                        index += 1
                    else:
                        updated_columns.append(column_obj)
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