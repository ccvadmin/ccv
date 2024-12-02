from odoo import models, fields, api
import logging
import datetime
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError

from ..lib.report import LibraryReport
libary_report = LibraryReport()

_logger = logging.getLogger(__name__)

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    @api.model
    def convert_money(self, value):
        return libary_report.convert_money(value)

    @api.model
    def convert_vnd(self, value):
        return libary_report.convert_vnd(value)

    @api.model
    def convert_date(self, value):
        return libary_report.convert_date(value)

    @api.model
    def convert_print(self, value):
        return libary_report.convert_print(value)

    partner_bank_id = fields.Many2one('res.partner.bank', string="Đơn vị/Cá nhân Thụ Hưởng")
    payment_type = fields.Selection(string="Hình thức thanh toán", selection=[('cash', 'Tiền mặt'), ('bank', 'Chuyển khoản')])

    def _prepare_payment_vals(self):
        res = super(HrExpenseSheet, self)._prepare_payment_vals()
        if self.partner_bank_id:
            res.update({
                'partner_bank_id': self.partner_bank_id.id
            })
        return res
    def _prepare_bill_vals(self):
        res = super(HrExpenseSheet, self)._prepare_bill_vals()
        if self.partner_bank_id:
            res.update({
                'partner_bank_id': self.partner_bank_id.id
            })
        return res
