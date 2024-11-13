from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class BetaLineTongHopCongNo(models.TransientModel):
    _name = "report.line.mixin"
    _description = "Report Mixin"
    
    partner_id = fields.Many2one('res.partner', string="Khách hàng", readonly=True)
    account_id = fields.Many2one('account.account', string="Tài khoản", readonly=True)
    account_dest_id = fields.Many2one('account.account', string="Tài khoản đích", readonly=True)
    parent_id = fields.Many2one('alpha.report', readonly=True)

    # Tiền gốc (Local currency)
    start_credit = fields.Float(string="Có đầu kỳ", default=0, digits=(16, 0))
    start_debit = fields.Float(string="Nợ đầu kỳ", default=0, digits=(16, 0))
    
    ps_credit = fields.Float(string="PS có", default=0, digits=(16, 0))
    ps_debit = fields.Float(string="PS nợ", default=0, digits=(16, 0))
    
    end_credit = fields.Float(string="Có cuối kỳ", compute="_compute_end_balance", store=True)
    end_debit = fields.Float(string="Nợ cuối kỳ", compute="_compute_end_balance", store=True)

    # Ngoại tệ (Foreign currency)
    start_credit_nt = fields.Float(string="Có đầu kỳ (Ngoại tệ)", default=0, digits=(16, 2))
    start_debit_nt = fields.Float(string="Nợ đầu kỳ (Ngoại tệ)", default=0, digits=(16, 2))
    
    ps_credit_nt = fields.Float(string="PS có (Ngoại tệ)", default=0, digits=(16, 2))
    ps_debit_nt = fields.Float(string="PS nợ (Ngoại tệ)", default=0, digits=(16, 2))
    
    end_credit_nt = fields.Float(string="Có cuối kỳ (Ngoại tệ)", compute="_compute_end_balance_nt", store=True, digits=(16, 2))
    end_debit_nt = fields.Float(string="Nợ cuối kỳ (Ngoại tệ)", compute="_compute_end_balance_nt", store=True, digits=(16, 2))

    # Field phát triển

    is_foreign_currency = fields.Boolean("Ngoại tệ", compute="_compute_foreign_currency")
    
    #########################################
    ###############  COMPUTE  ###############
    #########################################
    
    @api.depends('start_credit', 'start_debit', 'ps_credit', 'ps_debit')
    def _compute_end_balance(self):
        for record in self:
            sub_credit_debit = record.start_credit - record.start_debit
            if sub_credit_debit > 0:
                record.start_credit = sub_credit_debit
                record.start_debit = 0
            else:
                record.start_credit = 0
                record.start_debit = sub_credit_debit * -1
            end = (record.start_credit + record.ps_credit) - (record.ps_debit + record.start_debit)
            record.end_credit = end if end > 0 else 0
            record.end_debit = end * -1 if end < 0 else 0

    @api.depends('start_credit_nt', 'start_debit_nt', 'ps_credit_nt', 'ps_debit_nt')
    def _compute_end_balance_nt(self):
        for record in self:
            sub_credit_debit_nt = record.start_credit_nt - record.start_debit_nt
            if sub_credit_debit_nt > 0:
                record.start_credit_nt = sub_credit_debit_nt
                record.start_debit_nt = 0
            else:
                record.start_credit_nt = 0
                record.start_debit_nt = sub_credit_debit_nt * -1
            end_nt = (record.start_credit_nt + record.ps_credit_nt) - (record.ps_debit_nt + record.start_debit_nt)
            record.end_credit_nt = end_nt if end_nt > 0 else 0
            record.end_debit_nt = end_nt * -1 if end_nt < 0 else 0
    
    @api.depends("parent_id.is_foreign_currency")
    def _compute_foreign_currency(self):
        for line in self:
            line.is_foreign_currency = line.parent_id.is_foreign_currency

    ##########################################
    ###############  FUNCTION  ###############
    ##########################################

    def get_selected_fields(self, selected_fields=[]):
        if selected_fields:
            result = {}
            for field in selected_fields:
                result[field] = getattr(self, field, None)
            return result
        return False
