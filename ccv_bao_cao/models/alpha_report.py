from odoo import models, fields, api
import logging
import datetime
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)


class AlphaReport(models.TransientModel):
    _name = "alpha.report"
    # _inherit = "alpha.report"

    type = fields.Selection(
        # selection_add=[
        #     ("tong_hop_cong_no_phai_thu", "Tổng hợp công nợ phải thu"),
        #     ("tong_hop_cong_no_phai_tra", "Tổng hợp công nợ phải trả"),
        #     ("tong_hop_cong_no_phai_thu_usd", "Tổng hợp công nợ phải thu USD"),
        #     ("tong_hop_cong_no_phai_tra_usd", "Tổng hợp công nợ phải trả USD"),
        # ]
        selection=[
            ("tong_hop_cong_no_phai_thu", "Tổng hợp công nợ phải thu"),
            ("tong_hop_cong_no_phai_tra", "Tổng hợp công nợ phải trả"),
            ("tong_hop_cong_no_phai_thu_usd", "Tổng hợp công nợ phải thu USD"),
            ("tong_hop_cong_no_phai_tra_usd", "Tổng hợp công nợ phải trả USD"),
        ]
    )

    beta_line1_ids = fields.One2many("beta.report.line1",'parent_id', string="Tong hop cong no phai thu")
    beta_line2_ids = fields.One2many("beta.report.line2",'parent_id', string="Tong hop cong no phai tra")
    beta_line3_ids = fields.One2many("beta.report.line3",'parent_id', string="Tong hop cong no phai thu USD")
    beta_line4_ids = fields.One2many("beta.report.line4",'parent_id', string="Tong hop cong no phai tra USD")

    is_foreign_currency = fields.Boolean("Ngoại tệ", compute="_compute_foreign_currency")

    @api.depends("type")
    def _compute_foreign_currency(self):
        if self.type in [
            "tong_hop_cong_no_phai_thu_usd",
            "tong_hop_cong_no_phai_tra_usd",
        ]:
            self.is_foreign_currency = True
        else:
            self.is_foreign_currency = False

    def action_confirm(self):
        if self.type in [
            "tong_hop_cong_no_phai_tra",
            "tong_hop_cong_no_phai_thu",
            "tong_hop_cong_no_phai_thu_usd",
            "tong_hop_cong_no_phai_tra_usd",
        ]:
            return getattr(self, "get_row_data_" + self.type)()
        return super(AlphaReport, self).action_confirm()

    def action_view_tree(self):
        if self.type in [
            "tong_hop_cong_no_phai_tra",
            "tong_hop_cong_no_phai_thu",
            "tong_hop_cong_no_phai_thu_usd",
            "tong_hop_cong_no_phai_tra_usd",
        ]:
            return self.beta_view_tree(self.type)
        return super(AlphaReport, self).action_view_tree()

    def action_print_report(self):
        if self.type in [
            "tong_hop_cong_no_phai_tra",
            "tong_hop_cong_no_phai_thu",
            "tong_hop_cong_no_phai_thu_usd",
            "tong_hop_cong_no_phai_tra_usd",
        ]:
            return getattr(self, self.type + "_report")()
        return super(AlphaReport, self).action_print_report()

    ##########################################
    ###############  GỌI VIEW  ###############
    ##########################################

    def beta_view_tree(self, report_type):
        return self._get_action_view(report_type + "_beta_view_tree")

    def _get_action_view(self, view_name):
        action = self.env.ref('ccv_bao_cao.%s' % view_name)

        if action:
            return action
        else:
            return {
                "type": "ir.actions.act_window",
                "res_model": "alpha.report",
                "view_mode": "tree",
                "target": "current",
            }

    ###########################################
    ############  HÀM XUẤT REPORT  ############
    ###########################################

    def tong_hop_cong_no_phai_thu_report(self):
        data = {
            "account_id": self.account_id.id,
            "date_start": self.date_from.strftime("%d/%m/%Y"),
            "date_end": self.date_to.strftime("%d/%m/%Y"),
            "data": getattr(self, "get_data_export_" + self.type)(),
        }
        return self.env.ref(
            "ccv_bao_cao.tong_hop_cong_no_phai_thu_report"
        ).report_action(None, data=data)

    def tong_hop_cong_no_phai_tra_report(self):
        data = {
            "account_id": self.account_id.id,
            "date_start": self.date_from.strftime("%d/%m/%Y"),
            "date_end": self.date_to.strftime("%d/%m/%Y"),
            "data": getattr(self, "get_data_export_" + self.type)(),
        }
        return self.env.ref(
            "ccv_bao_cao.tong_hop_cong_no_phai_tra_report"
        ).report_action(None, data=data)

    def tong_hop_cong_no_phai_thu_usd_report(self):
        data = {
            "account_id": self.account_id.id,
            "date_start": self.date_from.strftime("%d/%m/%Y"),
            "date_end": self.date_to.strftime("%d/%m/%Y"),
            "data": getattr(self, "get_data_export_" + self.type)(),
        }
        return self.env.ref(
            "ccv_bao_cao.tong_hop_cong_no_phai_thu_usd_report"
        ).report_action(None, data=data)

    def tong_hop_cong_no_phai_tra_usd_report(self):
        data = {
            "account_id": self.account_id.id,
            "date_start": self.date_from.strftime("%d/%m/%Y"),
            "date_end": self.date_to.strftime("%d/%m/%Y"),
            "data": getattr(self, "get_data_export_" + self.type)(),
        }
        return self.env.ref(
            "ccv_bao_cao.tong_hop_cong_no_phai_tra_usd_report"
        ).report_action(None, data=data)

    ###########################################
    ###############  RUN QUERY  ###############
    ###########################################

    def get_row_data_tong_hop_cong_no_phai_thu(self):
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        partner_ids = self.env["res.partner"].search([]).mapped('id')
        query = [
            "select * from function_tong_hop_cong_no_phai_thu_1_kh('%s','%s', %s,%s,%s,%s)"
            % (
                date_start,
                date_end,
                self.account_id.id,
                partner_id,
                self.env.user.id,
                self.id,
            )
            for partner_id in partner_ids
        ]
        self.env.cr.execute("; ".join(query))
        result = self.env.cr.fetchall()
        return result

    def get_row_data_tong_hop_cong_no_phai_tra(self):
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        partner_ids = self.env["res.partner"].search([]).mapped('id')
        query = [
            "select * from function_tong_hop_cong_no_phai_tra_1_kh('%s','%s', %s,%s,%s,%s)"
            % (
                date_start,
                date_end,
                self.account_id.id,
                partner_id,
                self.env.user.id,
                self.id,
            )
            for partner_id in partner_ids
        ]
        self.env.cr.execute("; ".join(query))
        result = self.env.cr.fetchall()
        return result

    def get_row_data_tong_hop_cong_no_phai_thu_usd(self):
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        date_currency = self.date_to.strftime("%Y-%m-%d")
        partner_ids = self.env["res.partner"].search([]).mapped('id')
        query = [
            "select * from function_tong_hop_cong_no_phai_thu_usd_1_kh('%s','%s','%s',%s,%s,%s,%s)"
            % (
                date_start,
                date_end,
                date_currency,
                self.env.user.company_id.id,
                self.account_id.id,
                partner_id,
                self.env.user.id,
            )
            for partner_id in partner_ids
        ]
        self.env.cr.execute("; ".join(query))
        result = self.env.cr.fetchall()
        return result

    def get_row_data_tong_hop_cong_no_phai_tra_usd(self):
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        date_currency = self.date_to.strftime("%Y-%m-%d")
        partner_ids = self.env["res.partner"].search([]).mapped('id')
        query = [
            "select * from function_tong_hop_cong_no_phai_tra_usd_1_kh('%s','%s','%s',%s,%s,%s,%s)"
            % (
                date_start,
                date_end,
                date_currency,
                self.env.user.company_id.id,
                self.account_id.id,
                partner_id,
                self.env.user.id,
            )
            for partner_id in partner_ids
        ]
        self.env.cr.execute("; ".join(query))
        result = self.env.cr.fetchall()
        return result

    ##########################################
    #############  HÀM LẤY DATA  #############
    ##########################################

    def get_data_export_tong_hop_cong_no_phai_thu(self):
        sum_start_credit = sum(self.beta_line1_ids.mapped("start_credit"))
        sum_start_debit = sum(self.beta_line1_ids.mapped("start_debit"))
        sum_ps_credit = sum(self.beta_line1_ids.mapped("ps_credit"))
        sum_ps_debit = sum(self.beta_line1_ids.mapped("ps_debit"))
        sum_end_credit = sum(self.beta_line1_ids.mapped("end_credit"))
        sum_end_debit = sum(self.beta_line1_ids.mapped("end_debit"))
        lines = []
        count = 1
        for data in self.beta_line1_ids:
            customer_name   = data.customer_name
            customer_code   = data.customer_code
            customer_group  = data.customer_group
            start_credit    = data.start_credit
            start_debit     = data.start_debit
            ps_credit       = data.ps_credit
            ps_debit        = data.ps_debit
            end_credit      = data.end_credit
            end_debit       = data.end_debit

            if (
                start_credit == 0
                and start_debit == 0
                and ps_credit == 0
                and ps_debit == 0
            ):
                continue

            vals = {
                "no": count,
                "customer_name": customer_name,
                "customer_code": customer_code,
                "customer_group": customer_group,
                "start_credit": f"{start_credit:,}",
                "start_debit": f"{start_debit:,}",
                "ps_credit": f"{ps_credit:,}",
                "ps_debit": f"{ps_debit:,}",
                "end_credit": f"{end_credit:,}",
                "end_debit": f"{end_debit:,}",
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_start_credit": f"{sum_start_credit:,}",
                "sum_start_debit": f"{sum_start_debit:,}",
                "sum_ps_credit": f"{sum_ps_credit:,}",
                "sum_ps_debit": f"{sum_ps_debit:,}",
                "sum_end_credit": f"{sum_end_credit:,}",
                "sum_end_debit": f"{sum_end_debit:,}",
            },
            "lines": lines,
        }

    def get_data_export_tong_hop_cong_no_phai_tra(self):
        sum_start_credit = sum(self.beta_line2_ids.mapped("start_credit"))
        sum_start_debit = sum(self.beta_line2_ids.mapped("start_debit"))
        sum_ps_credit = sum(self.beta_line2_ids.mapped("ps_credit"))
        sum_ps_debit = sum(self.beta_line2_ids.mapped("ps_debit"))
        sum_end_credit = sum(self.beta_line2_ids.mapped("end_credit"))
        sum_end_debit = sum(self.beta_line2_ids.mapped("end_debit"))
        lines = []
        count = 1
        for data in self.beta_line2_ids:
            customer_name   = data.customer_name
            customer_code   = data.customer_code
            address         = data.address
            vat             = data.vat
            start_credit    = data.start_credit
            start_debit     = data.start_debit
            ps_credit       = data.ps_credit
            ps_debit        = data.ps_debit
            end_credit      = data.end_credit
            end_debit       = data.end_debit

            if (
                start_credit == 0
                and start_debit == 0
                and ps_credit == 0
                and ps_debit == 0
            ):
                continue

            vals = {
                "no": count,
                "customer_name": customer_name,
                "customer_code": customer_code,
                "address": address,
                "vat": vat,
                "start_credit": f"{int(start_credit):,}",
                "start_debit": f"{int(start_debit):,}",
                "ps_credit": f"{int(ps_credit):,}",
                "ps_debit": f"{int(ps_debit):,}",
                "end_credit": f"{int(end_credit):,}",
                "end_debit": f"{int(end_debit):,}",
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_start_credit": f"{sum_start_credit:,}",
                "sum_start_debit": f"{sum_start_debit:,}",
                "sum_ps_credit": f"{sum_ps_credit:,}",
                "sum_ps_debit": f"{sum_ps_debit:,}",
                "sum_end_credit": f"{sum_end_credit:,}",
                "sum_end_debit": f"{sum_end_debit:,}",
            },
            "lines": lines,
        }

    def get_data_export_tong_hop_cong_no_phai_thu_usd(self):
        sum_start_credit_usd = sum(self.beta_line1_ids.mapped("start_credit_nt"))
        sum_start_debit_usd = sum(self.beta_line1_ids.mapped("start_debit_nt"))
        sum_ps_credit_usd = sum(self.beta_line1_ids.mapped("ps_credit_nt"))
        sum_ps_debit_usd = sum(self.beta_line1_ids.mapped("ps_debit_nt"))
        sum_end_credit_usd = sum(self.beta_line1_ids.mapped("end_credit_nt"))
        sum_end_debit_usd = sum(self.beta_line1_ids.mapped("end_debit_nt"))

        sum_start_credit_vnd = sum(self.beta_line1_ids.mapped("start_credit"))
        sum_start_debit_vnd = sum(self.beta_line1_ids.mapped("start_debit"))
        sum_ps_credit_vnd = sum(self.beta_line1_ids.mapped("ps_credit"))
        sum_ps_debit_vnd = sum(self.beta_line1_ids.mapped("ps_debit"))
        sum_end_credit_vnd = sum(self.beta_line1_ids.mapped("end_credit"))
        sum_end_debit_vnd = sum(self.beta_line1_ids.mapped("end_debit"))

        lines = []
        count = 1
        for data in self.beta_line3_ids:
            customer_code       = data.customer_code
            customer_name       = data.customer_name
            address             = data.address
            vat                 = data.vat
            account_id          = data.account_id.code
            start_debit_usd     = data.start_debit_nt
            start_debit_vnd     = data.start_debit
            start_credit_usd    = data.start_credit_nt
            start_credit_vnd    = data.start_credit
            ps_debit_usd        = data.ps_debit_nt
            ps_debit_vnd        = data.ps_debit
            ps_credit_usd       = data.ps_credit_nt
            ps_credit_vnd       = data.ps_credit
            end_debit_usd       = data.end_debit_nt
            end_debit_vnd       = data.end_debit
            end_credit_usd      = data.end_credit_nt
            end_credit_vnd      = data.end_credit

            if (
                start_credit_usd == 0
                and start_debit_usd == 0
                and ps_credit_usd == 0
                and ps_debit_usd == 0
            ):
                continue

            vals = {
                "no": count,
                "customer_code": customer_code,
                "customer_name": customer_name,
                "address": address,
                "vat": vat,
                "account_id": account_id,
                "start_debit_usd": round(start_debit_usd, 2),
                "start_debit_vnd": round(start_debit_vnd),
                "start_credit_usd": round(start_credit_usd, 2),
                "start_credit_vnd": round(start_credit_vnd),
                "ps_debit_usd": round(ps_debit_usd, 2),
                "ps_debit_vnd": round(ps_debit_vnd),
                "ps_credit_usd": round(ps_credit_usd, 2),
                "ps_credit_vnd": round(ps_credit_vnd),
                "end_debit_usd": round(end_debit_usd, 2),
                "end_debit_vnd": round(end_debit_vnd),
                "end_credit_usd": round(end_credit_usd, 2),
                "end_credit_vnd": round(end_credit_vnd),
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_start_credit_vnd": f"{round(sum_start_credit_vnd):,}",
                "sum_start_debit_vnd": f"{round(sum_start_debit_vnd):,}",
                "sum_ps_credit_vnd": f"{round(sum_ps_credit_vnd):,}",
                "sum_ps_debit_vnd": f"{round(sum_ps_debit_vnd):,}",
                "sum_end_credit_vnd": f"{round(sum_end_credit_vnd):,}",
                "sum_end_debit_vnd": f"{round(sum_end_debit_vnd):,}",
                "sum_start_credit_usd": f"{round(sum_start_credit_usd, 2):,}",
                "sum_start_debit_usd": f"{round(sum_start_debit_usd, 2):,}",
                "sum_ps_credit_usd": f"{round(sum_ps_credit_usd, 2):,}",
                "sum_ps_debit_usd": f"{round(sum_ps_debit_usd, 2):,}",
                "sum_end_credit_usd": f"{round(sum_end_credit_usd, 2):,}",
                "sum_end_debit_usd": f"{round(sum_end_debit_usd, 2):,}",
            },
            "lines": lines,
        }

    def get_data_export_tong_hop_cong_no_phai_tra_usd(self):
        sum_start_credit_usd = sum(self.beta_line1_ids.mapped("start_credit_nt"))
        sum_start_debit_usd = sum(self.beta_line1_ids.mapped("start_debit_nt"))
        sum_ps_credit_usd = sum(self.beta_line1_ids.mapped("ps_credit_nt"))
        sum_ps_debit_usd = sum(self.beta_line1_ids.mapped("ps_debit_nt"))
        sum_end_credit_usd = sum(self.beta_line1_ids.mapped("end_credit_nt"))
        sum_end_debit_usd = sum(self.beta_line1_ids.mapped("end_debit_nt"))

        sum_start_credit_vnd = sum(self.beta_line1_ids.mapped("start_credit"))
        sum_start_debit_vnd = sum(self.beta_line1_ids.mapped("start_debit"))
        sum_ps_credit_vnd = sum(self.beta_line1_ids.mapped("ps_credit"))
        sum_ps_debit_vnd = sum(self.beta_line1_ids.mapped("ps_debit"))
        sum_end_credit_vnd = sum(self.beta_line1_ids.mapped("end_credit"))
        sum_end_debit_vnd = sum(self.beta_line1_ids.mapped("end_debit"))

        lines = []
        count = 1
        for data in self.beta_line3_ids:
            customer_code       = data.customer_code
            customer_name       = data.customer_name
            address             = data.address
            vat                 = data.vat
            account_id          = data.account_id.code
            start_debit_usd     = data.start_debit_nt
            start_debit_vnd     = data.start_debit
            start_credit_usd    = data.start_credit_nt
            start_credit_vnd    = data.start_credit
            ps_debit_usd        = data.ps_debit_nt
            ps_debit_vnd        = data.ps_debit
            ps_credit_usd       = data.ps_credit_nt
            ps_credit_vnd       = data.ps_credit
            end_debit_usd       = data.end_debit_nt
            end_debit_vnd       = data.end_debit
            end_credit_usd      = data.end_credit_nt
            end_credit_vnd      = data.end_credit

            if (
                start_credit_usd == 0
                and start_debit_usd == 0
                and ps_credit_usd == 0
                and ps_debit_usd == 0
            ):
                continue
            vals = {
                "no": count,
                "customer_code": customer_code,
                "customer_name": customer_name,
                "address": address,
                "vat": vat,
                "account_id": account_id,
                "start_debit_usd": round(start_debit_usd, 2),
                "start_debit_vnd": round(start_debit_vnd),
                "start_credit_usd": round(start_credit_usd, 2),
                "start_credit_vnd": round(start_credit_vnd),
                "ps_debit_usd": round(ps_debit_usd, 2),
                "ps_debit_vnd": round(ps_debit_vnd),
                "ps_credit_usd": round(ps_credit_usd, 2),
                "ps_credit_vnd": round(ps_credit_vnd),
                "end_debit_usd": round(end_debit_usd, 2),
                "end_debit_vnd": round(end_debit_vnd),
                "end_credit_usd": round(end_credit_usd, 2),
                "end_credit_vnd": round(end_credit_vnd),
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_start_credit_vnd": f"{round(sum_start_credit_vnd):,}",
                "sum_start_debit_vnd": f"{round(sum_start_debit_vnd):,}",
                "sum_ps_credit_vnd": f"{round(sum_ps_credit_vnd):,}",
                "sum_ps_debit_vnd": f"{round(sum_ps_debit_vnd):,}",
                "sum_end_credit_vnd": f"{round(sum_end_credit_vnd):,}",
                "sum_end_debit_vnd": f"{round(sum_end_debit_vnd):,}",
                "sum_start_credit_usd": f"{round(sum_start_credit_usd, 2):,}",
                "sum_start_debit_usd": f"{round(sum_start_debit_usd, 2):,}",
                "sum_ps_credit_usd": f"{round(sum_ps_credit_usd, 2):,}",
                "sum_ps_debit_usd": f"{round(sum_ps_debit_usd, 2):,}",
                "sum_end_credit_usd": f"{round(sum_end_credit_usd, 2):,}",
                "sum_end_debit_usd": f"{round(sum_end_debit_usd, 2):,}",
            },
            "lines": lines,
        }
