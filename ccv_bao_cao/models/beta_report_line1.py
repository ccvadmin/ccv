from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class BetaReportLine1(models.TransientModel):
    _name = "beta.report.line1"
    _description = "Tong Hop Cong No Phai Thu"
    _inherit = ["report.line.mixin"]

    customer_name = fields.Char(string="Tên khách hàng", default="")
    customer_code = fields.Char(string="Mã khách hàng", default="")
    customer_group = fields.Char(string="Mã nhóm khách hàng", default="")

    # @api.depends('partner_id')
    # def _compute_info(self):
    #     for record in self:
    #         if record.partner_id:
    #             record.customer_name = record.partner_id.name
    #             record.customer_code = record.partner_id.code_contact
    #             customer_group = []
    #             category_ids = record.partner_id.category_id.mapped('name')
    #             if category_ids:
    #                 customer_group = [category_name for category_name in category_ids if 'KH -' in category_name]
    #             record.customer_group = customer_group[0].split(' - ')[1] if customer_group else ""
    #         else:
    #             record.customer_name = ""
    #             record.customer_code = ""
    #             record.customer_group = ""