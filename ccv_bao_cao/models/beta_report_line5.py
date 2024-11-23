from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class BetaReportLine5(models.TransientModel):
    _name = "beta.report.line5"
    _description = "Chi tiết công nợ phải trả USD"
    _inherit = ["report.line.mixin"]

    @api.depends('ps_credit', 'ps_debit')
    def _compute_end_balance(self):
        records = self.parent_id.beta_line5_ids
        dau_ky = records.filtered(lambda l: l.account_id is False)
        end_credit = dau_ky.end_credit
        end_debit = dau_ky.end_debit
        current_balance = end_debit - end_credit

        def compute_balance(record, sub):
            if sub < 0:
                record.end_credit = abs(sub)
                record.end_debit = 0
            else:
                record.end_credit = 0
                record.end_debit = abs(sub)

        compute_balance(dau_ky, current_balance)

        ps = records.filtered(lambda l: l.account_id is not False)

        for record in ps:
            if record.ps_credit != 0:
                current_balance -= record.ps_credit
            else:
                current_balance += record.ps_debit
            compute_balance(record, current_balance)

    @api.depends('ps_credit_nt', 'ps_debit_nt')
    def _compute_end_balance_nt(self):
        records = self.parent_id.beta_line5_ids
        dau_ky = records.filtered(lambda l: l.account_id is False)
        end_credit_nt = dau_ky.end_credit_nt
        end_debit_nt = dau_ky.end_debit_nt

        current_balance = end_debit_nt - end_credit_nt

        def compute_balance(record, sub):
            if sub < 0:
                record.end_credit_nt = abs(sub)
                record.end_debit_nt = 0
            else:
                record.end_credit_nt = 0
                record.end_debit_nt = abs(sub)

        compute_balance(dau_ky, current_balance)

        ps = records.filtered(lambda l: l.account_id is not False)

        for record in ps:
            if record.ps_credit != 0:
                current_balance -= record.ps_credit_nt
            else:
                current_balance += record.ps_debit_nt
            compute_balance(record, current_balance)
