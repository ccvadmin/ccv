from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class BetaReportLine4(models.TransientModel):
    _name = "beta.report.line4"
    _description = "Tổng hợp công nợ phải trả USD"
    _inherit = ["report.line.mixin"]

    customer_name = fields.Char(string="Tên nhà cung cấp", default="")
    customer_code = fields.Char(string="Mã nhà cung cấp", default="")
    address = fields.Char(string="Địa chỉ", default="")
    vat = fields.Char(string="Mã số thuế", default="")

    @api.depends('partner_id')
    def _compute_info(self):
        for record in self:
            if record.partner_id:
                record.customer_name = record.partner_id.name
                record.customer_code = record.partner_id.code_contact
                record.address = record.partner_id.street
                record.vat = record.partner_id.vat
            else:
                record.customer_name = ""
                record.customer_code = ""
                record.address = ""
                record.vat = ""
