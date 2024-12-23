from odoo import models, fields, api
import logging
import datetime
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ALL_TYPE = {
    "tong_hop_cong_no_phai_thu": ("Tổng hợp công nợ phải thu", 'beta.report.line1', 'beta_line1_ids'),
    "tong_hop_cong_no_phai_tra": ("Tổng hợp công nợ phải trả", 'beta.report.line2', 'beta_line2_ids'),
    "tong_hop_cong_no_phai_thu_usd": ("Tổng hợp công nợ phải thu USD", 'beta.report.line3', 'beta_line3_ids'),
    "tong_hop_cong_no_phai_tra_usd": ("Tổng hợp công nợ phải trả USD", 'beta.report.line4', 'beta_line4_ids'),
    "chi_tiet_cong_no_phai_tra_usd": ("Chi tiết công nợ phải trả USD", 'beta.report.line5', 'beta_line5_ids'),
    "chi_tiet_cong_no_phai_thu_usd": ("Chi tiết công nợ phải thu USD", 'beta.report.line6', 'beta_line6_ids'),
}

ALL_TYPE_NT = [
    "tong_hop_cong_no_phai_thu_usd",
    "tong_hop_cong_no_phai_tra_usd",
    "chi_tiet_cong_no_phai_tra_usd",
    "chi_tiet_cong_no_phai_thu_usd",
]

contrainst = {
    'account_id': "Tài khoản",
    'date_from': "Ngày bắt đầu",
    'date_to': "Ngày kết thúc",
    'partner_id': "Khách hàng",
}
class AlphaReport(models.TransientModel):
    _inherit = "alpha.report"

    type = fields.Selection(selection_add=[(key, value[0])for key,value in ALL_TYPE.items()])

    beta_line1_ids = fields.One2many("beta.report.line1",'parent_id', string="Tong hop cong no phai thu")
    beta_line2_ids = fields.One2many("beta.report.line2",'parent_id', string="Tong hop cong no phai tra")
    beta_line3_ids = fields.One2many("beta.report.line3",'parent_id', string="Tong hop cong no phai thu USD")
    beta_line4_ids = fields.One2many("beta.report.line4",'parent_id', string="Tong hop cong no phai tra USD")
    beta_line5_ids = fields.One2many("beta.report.line5",'parent_id', string="Chi tiết công nợ phai tra USD")
    beta_line6_ids = fields.One2many("beta.report.line6",'parent_id', string="Chi tiết cong no phai thu USD")

    is_foreign_currency = fields.Boolean("Ngoại tệ", compute="_compute_foreign_currency")

    @api.depends("type")
    def _compute_foreign_currency(self):
        if self.type in ALL_TYPE_NT:
            self.is_foreign_currency = True
        else:
            self.is_foreign_currency = False

    def action_confirm(self):
        if self.type in ALL_TYPE.keys():
            return getattr(self, "get_row_data_" + self.type)()
        return super(AlphaReport, self).action_confirm()

    def action_view_tree(self):
        if self.type in ALL_TYPE.keys():
            return self.beta_view_tree(self.type)
        return super(AlphaReport, self).action_view_tree()

    def action_print_report(self):
        if self.type in ALL_TYPE.keys():
            return self.beta_action_export_report()
        return super(AlphaReport, self).action_print_report()

    ##########################################
    ###############  GỌI VIEW  ###############
    ##########################################

    def beta_view_tree(self, report_type):
        ids = []
        domain = []
        model_name = ""
        title = ""
        if report_type in ALL_TYPE:
            title, model_name, line_ids_field = ALL_TYPE[report_type]
            ids = getattr(self, line_ids_field).ids
            if ids:
                domain = [('id', 'in', ids)]
        return self._get_action_view(title, model_name, domain)


    def _get_action_view(self, title, model_name, domain=[]):
        return {
            'name': title,
            'res_model': model_name,
            'view_mode': 'tree',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain' : domain or []
        }


    ###########################################
    ############  HÀM XUẤT REPORT  ############
    ###########################################

    def generate_prepare_value_tong_hop_cong_no_phai_thu(self):
        return {
            "account_id"    : self.account_id.id,
            "date_start"    : self.date_from.strftime("%d/%m/%Y"),
            "date_end"      : self.date_to.strftime("%d/%m/%Y"),
            "data"          : getattr(self, "get_data_export_" + self.type)(),
        }
    
    def generate_prepare_value_tong_hop_cong_no_phai_tra(self):
        return {
            "account_id"    : self.account_id.id,
            "date_start"    : self.date_from.strftime("%d/%m/%Y"),
            "date_end"      : self.date_to.strftime("%d/%m/%Y"),
            "data"          : getattr(self, "get_data_export_" + self.type)(),
        }
    
    def generate_prepare_value_tong_hop_cong_no_phai_thu_usd(self):
        return {
            "account_id"    : self.account_id.id,
            "date_start"    : self.date_from.strftime("%d/%m/%Y"),
            "date_end"      : self.date_to.strftime("%d/%m/%Y"),
            "data"          : getattr(self, "get_data_export_" + self.type)(),
        }
    
    def generate_prepare_value_tong_hop_cong_no_phai_tra_usd(self):
        return {
            "account_id"    : self.account_id.id,
            "date_start"    : self.date_from.strftime("%d/%m/%Y"),
            "date_end"      : self.date_to.strftime("%d/%m/%Y"),
            "data"          : getattr(self, "get_data_export_" + self.type)(),
        }
    
    def generate_prepare_value_chi_tiet_cong_no_phai_tra_usd(self):
        return {
            "account_id"    : self.account_id.code,
            "partner_id"    : self.partner_id.name,
            "date_start"    : self.date_from.strftime("%d/%m/%Y"),
            "date_end"      : self.date_to.strftime("%d/%m/%Y"),
            "data"          : getattr(self, "get_data_export_" + self.type)(),
        }
    
    def generate_prepare_value_chi_tiet_cong_no_phai_thu_usd(self):
        return {
            "account_id"    : self.account_id.code,
            "partner_id"    : self.partner_id.name,
            "date_start"    : self.date_from.strftime("%d/%m/%Y"),
            "date_end"      : self.date_to.strftime("%d/%m/%Y"),
            "data"          : getattr(self, "get_data_export_" + self.type)(),
        }

    def generate_prepare_value(self):
        return getattr(self, "generate_prepare_value_%s" % self.type)()

    def beta_action_export_report(self):
        data = self.generate_prepare_value()
        return self.env.ref("ccv_bao_cao.%s_report" % self.type).report_action(None, data=data)

    ###########################################
    ###############  RUN QUERY  ###############
    ###########################################

    # TODO: Dynamic hóa

    def check_invalid(self, keys = []):
        for key in keys:
            if not getattr(self, key, False):
                raise UserError("Vui lòng chọn %s!!!" % contrainst.get(key, ""))

    def get_row_data_tong_hop_cong_no_phai_thu(self):
        self.check_invalid(['date_from', 'date_to', 'account_id'])
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        # partner_ids = self.env["res.partner"].search([]).mapped('id')
        partner_ids = list(set(self.env['account.move'].search([]).mapped('partner_id').mapped('id')))
        self.env.cr.execute("delete from beta_report_line1 where parent_id = %s;" % self.id)
        query = [
            "select * from function_tong_hop_cong_no_phai_thu_1_kh('%s','%s', %s,%s,%s,%s)"
            % (date_start, date_end, self.account_id.id, partner_id, self.env.user.id, self.id)
            for partner_id in partner_ids
        ]
        self.env.cr.execute("; ".join(query))
        result = self.env.cr.fetchall()
        self.beta_line1_ids._compute_end_balance()
        return result

    def get_row_data_tong_hop_cong_no_phai_tra(self):
        self.check_invalid(['date_from', 'date_to', 'account_id'])
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        # partner_ids = self.env["res.partner"].search([]).mapped('id')
        partner_ids = list(set(self.env['account.move'].search([]).mapped('partner_id').mapped('id')))
        self.env.cr.execute("delete from beta_report_line2 where parent_id = %s;" % self.id)
        query = [
            "select * from function_tong_hop_cong_no_phai_tra_1_kh('%s','%s', %s,%s,%s,%s)"
            % (date_start, date_end, self.account_id.id, partner_id, self.env.user.id, self.id)
            for partner_id in partner_ids
        ]
        self.env.cr.execute("; ".join(query))
        result = self.env.cr.fetchall()
        self.beta_line2_ids._compute_end_balance()
        return result

    def get_row_data_tong_hop_cong_no_phai_thu_usd(self):
        self.check_invalid(['date_from', 'date_to', 'account_id'])
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        # date_currency = self.date_to.strftime("%Y-%m-%d")
        # partner_ids = self.env["res.partner"].search([]).mapped('id')
        partner_ids = list(set(self.env['account.move'].search([]).mapped('partner_id').mapped('id')))
        self.env.cr.execute("delete from beta_report_line3 where parent_id = %s;" % self.id)
        query = [
            "select * from function_tong_hop_cong_no_phai_thu_usd_1_kh('%s','%s',%s,%s,%s,%s,%s)"
            % (date_start, date_end, self.env.user.company_id.id, self.account_id.id, partner_id, self.env.user.id, self.id)
            for partner_id in partner_ids
        ]
        self.env.cr.execute("; ".join(query))
        result = self.env.cr.fetchall()
        self.beta_line3_ids._compute_end_balance()
        self.beta_line3_ids._compute_end_balance_nt()
        return result

    def get_row_data_tong_hop_cong_no_phai_tra_usd(self):
        self.check_invalid(['date_from', 'date_to', 'account_id'])
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        # date_currency = self.date_to.strftime("%Y-%m-%d")
        # partner_ids = self.env["res.partner"].search([]).mapped('id')
        partner_ids = list(set(self.env['account.move'].search([]).mapped('partner_id').mapped('id')))
        self.env.cr.execute("delete from beta_report_line4 where parent_id = %s;" % self.id)
        query = [
            "select * from function_tong_hop_cong_no_phai_tra_usd_1_kh('%s','%s',%s,%s,%s,%s,%s)"
            % (date_start, date_end, self.env.user.company_id.id, self.account_id.id, partner_id, self.env.user.id, self.id)
            for partner_id in partner_ids
        ]
        self.env.cr.execute("; ".join(query))
        result = self.env.cr.fetchall()
        self.beta_line4_ids._compute_end_balance()
        self.beta_line4_ids._compute_end_balance_nt()
        return result

    def get_row_data_chi_tiet_cong_no_phai_tra_usd(self):
        self.check_invalid(['date_from', 'date_to', 'account_id', 'partner_id'])
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        query = "select * from function_chi_tiet_cong_no_phai_tra_usd('%s','%s',%s,%s,%s,%s)" \
            % (date_start, date_end, self.env.user.company_id.id, self.account_id.id, self.partner_id.id, self.id)
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        self.beta_line5_ids._compute_end_balance()
        self.beta_line5_ids._compute_end_balance_nt()
        return result

    def get_row_data_chi_tiet_cong_no_phai_thu_usd(self):
        self.check_invalid(['date_from', 'date_to', 'account_id', 'partner_id'])
        date_start = self.date_from.strftime("%Y%m%d")
        date_end = self.date_to.strftime("%Y%m%d")
        query = "select * from function_chi_tiet_cong_no_phai_thu_usd('%s','%s',%s,%s,%s,%s)" \
            % (date_start, date_end, self.env.user.company_id.id, self.account_id.id, self.partner_id.id, self.id)
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        self.beta_line6_ids._compute_end_balance()
        self.beta_line6_ids._compute_end_balance_nt()
        return result

    ##########################################
    #############  HÀM LẤY DATA  #############
    ##########################################

    # TODO: Dynamic hóa

    def get_data_export_tong_hop_cong_no_phai_thu(self):
        sum_start_credit    = sum(self.beta_line1_ids.mapped("start_credit"))
        sum_start_debit     = sum(self.beta_line1_ids.mapped("start_debit"))
        sum_ps_credit       = sum(self.beta_line1_ids.mapped("ps_credit"))
        sum_ps_debit        = sum(self.beta_line1_ids.mapped("ps_debit"))
        sum_end_credit      = sum(self.beta_line1_ids.mapped("end_credit"))
        sum_end_debit       = sum(self.beta_line1_ids.mapped("end_debit"))
        lines = []
        count = 1
        for data in self.beta_line1_ids:
            customer_name   = data.customer_name if data.customer_name else ""
            customer_code   = data.customer_code if data.customer_code else ""
            customer_group  = data.customer_group if data.customer_group else ""
            start_credit    = data.start_credit
            start_debit     = data.start_debit
            ps_credit       = data.ps_credit
            ps_debit        = data.ps_debit
            end_credit      = data.end_credit
            end_debit       = data.end_debit

            if (
                start_credit    == 0
                and start_debit == 0
                and ps_credit   == 0
                and ps_debit    == 0
            ):
                continue

            vals = {
                "no"                : count,
                "customer_name"     : customer_name,
                "customer_code"     : customer_code,
                "customer_group"    : customer_group,
                "start_credit"      : f"{start_credit:,}",
                "start_debit"       : f"{start_debit:,}",
                "ps_credit"         : f"{ps_credit:,}",
                "ps_debit"          : f"{ps_debit:,}",
                "end_credit"        : f"{end_credit:,}",
                "end_debit"         : f"{end_debit:,}",
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_start_credit"  : f"{sum_start_credit:,}",
                "sum_start_debit"   : f"{sum_start_debit:,}",
                "sum_ps_credit"     : f"{sum_ps_credit:,}",
                "sum_ps_debit"      : f"{sum_ps_debit:,}",
                "sum_end_credit"    : f"{sum_end_credit:,}",
                "sum_end_debit"     : f"{sum_end_debit:,}",
            },
            "lines": lines,
        }

    def get_data_export_tong_hop_cong_no_phai_tra(self):
        sum_start_credit    = sum(self.beta_line2_ids.mapped("start_credit"))
        sum_start_debit     = sum(self.beta_line2_ids.mapped("start_debit"))
        sum_ps_credit       = sum(self.beta_line2_ids.mapped("ps_credit"))
        sum_ps_debit        = sum(self.beta_line2_ids.mapped("ps_debit"))
        sum_end_credit      = sum(self.beta_line2_ids.mapped("end_credit"))
        sum_end_debit       = sum(self.beta_line2_ids.mapped("end_debit"))
        lines = []
        count = 1
        for data in self.beta_line2_ids:
            customer_name   = data.customer_name if data.customer_name else ""
            customer_code   = data.customer_code if data.customer_code else ""
            address         = data.address if data.address else ""
            vat             = data.vat if data.vat else ""
            start_credit    = data.start_credit
            start_debit     = data.start_debit
            ps_credit       = data.ps_credit
            ps_debit        = data.ps_debit
            end_credit      = data.end_credit
            end_debit       = data.end_debit

            if (
                start_credit    == 0
                and start_debit == 0
                and ps_credit   == 0
                and ps_debit    == 0
            ):
                continue

            vals = {
                "no"            : count,
                "customer_name" : customer_name,
                "customer_code" : customer_code,
                "address"       : address,
                "vat"           : vat,
                "start_credit"  : f"{int(start_credit):,}",
                "start_debit"   : f"{int(start_debit):,}",
                "ps_credit"     : f"{int(ps_credit):,}",
                "ps_debit"      : f"{int(ps_debit):,}",
                "end_credit"    : f"{int(end_credit):,}",
                "end_debit"     : f"{int(end_debit):,}",
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_start_credit"  : f"{sum_start_credit:,}",
                "sum_start_debit"   : f"{sum_start_debit:,}",
                "sum_ps_credit"     : f"{sum_ps_credit:,}",
                "sum_ps_debit"      : f"{sum_ps_debit:,}",
                "sum_end_credit"    : f"{sum_end_credit:,}",
                "sum_end_debit"     : f"{sum_end_debit:,}",
            },
            "lines": lines,
        }

    def get_data_export_tong_hop_cong_no_phai_thu_usd(self):
        sum_start_credit_usd    = sum(self.beta_line3_ids.mapped("start_credit_nt"))
        sum_start_debit_usd     = sum(self.beta_line3_ids.mapped("start_debit_nt"))
        sum_ps_credit_usd       = sum(self.beta_line3_ids.mapped("ps_credit_nt"))
        sum_ps_debit_usd        = sum(self.beta_line3_ids.mapped("ps_debit_nt"))
        sum_end_credit_usd      = sum(self.beta_line3_ids.mapped("end_credit_nt"))
        sum_end_debit_usd       = sum(self.beta_line3_ids.mapped("end_debit_nt"))

        sum_start_credit_vnd    = sum(self.beta_line3_ids.mapped("start_credit"))
        sum_start_debit_vnd     = sum(self.beta_line3_ids.mapped("start_debit"))
        sum_ps_credit_vnd       = sum(self.beta_line3_ids.mapped("ps_credit"))
        sum_ps_debit_vnd        = sum(self.beta_line3_ids.mapped("ps_debit"))
        sum_end_credit_vnd      = sum(self.beta_line3_ids.mapped("end_credit"))
        sum_end_debit_vnd       = sum(self.beta_line3_ids.mapped("end_debit"))

        lines = []
        count = 1
        for data in self.beta_line3_ids:
            customer_name       = data.customer_name if data.customer_name else ""
            customer_code       = data.customer_code if data.customer_code else ""
            address             = data.address if data.address else ""
            vat                 = data.vat if data.vat else ""
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
                start_credit_usd    == 0
                and start_debit_usd == 0
                and ps_credit_usd   == 0
                and ps_debit_usd    == 0
            ):
                continue

            vals = {
                "no"                : count,
                "customer_code"     : customer_code,
                "customer_name"     : customer_name,
                "address"           : address,
                "vat"               : vat,
                "account_id"        : account_id,
                "start_debit_usd"   : round(start_debit_usd, 2),
                "start_debit_vnd"   : round(start_debit_vnd),
                "start_credit_usd"  : round(start_credit_usd, 2),
                "start_credit_vnd"  : round(start_credit_vnd),
                "ps_debit_usd"      : round(ps_debit_usd, 2),
                "ps_debit_vnd"      : round(ps_debit_vnd),
                "ps_credit_usd"     : round(ps_credit_usd, 2),
                "ps_credit_vnd"     : round(ps_credit_vnd),
                "end_debit_usd"     : round(end_debit_usd, 2),
                "end_debit_vnd"     : round(end_debit_vnd),
                "end_credit_usd"    : round(end_credit_usd, 2),
                "end_credit_vnd"    : round(end_credit_vnd),
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_start_credit_vnd"  : f"{round(sum_start_credit_vnd):,}",
                "sum_start_debit_vnd"   : f"{round(sum_start_debit_vnd):,}",
                "sum_ps_credit_vnd"     : f"{round(sum_ps_credit_vnd):,}",
                "sum_ps_debit_vnd"      : f"{round(sum_ps_debit_vnd):,}",
                "sum_end_credit_vnd"    : f"{round(sum_end_credit_vnd):,}",
                "sum_end_debit_vnd"     : f"{round(sum_end_debit_vnd):,}",
                "sum_start_credit_usd"  : f"{round(sum_start_credit_usd, 2):,}",
                "sum_start_debit_usd"   : f"{round(sum_start_debit_usd, 2):,}",
                "sum_ps_credit_usd"     : f"{round(sum_ps_credit_usd, 2):,}",
                "sum_ps_debit_usd"      : f"{round(sum_ps_debit_usd, 2):,}",
                "sum_end_credit_usd"    : f"{round(sum_end_credit_usd, 2):,}",
                "sum_end_debit_usd"     : f"{round(sum_end_debit_usd, 2):,}",
            },
            "lines": lines,
        }

    def get_data_export_tong_hop_cong_no_phai_tra_usd(self):
        sum_start_credit_usd    = sum(self.beta_line4_ids.mapped("start_credit_nt"))
        sum_start_debit_usd     = sum(self.beta_line4_ids.mapped("start_debit_nt"))
        sum_ps_credit_usd       = sum(self.beta_line4_ids.mapped("ps_credit_nt"))
        sum_ps_debit_usd        = sum(self.beta_line4_ids.mapped("ps_debit_nt"))
        sum_end_credit_usd      = sum(self.beta_line4_ids.mapped("end_credit_nt"))
        sum_end_debit_usd       = sum(self.beta_line4_ids.mapped("end_debit_nt"))

        sum_start_credit_vnd    = sum(self.beta_line4_ids.mapped("start_credit"))
        sum_start_debit_vnd     = sum(self.beta_line4_ids.mapped("start_debit"))
        sum_ps_credit_vnd       = sum(self.beta_line4_ids.mapped("ps_credit"))
        sum_ps_debit_vnd        = sum(self.beta_line4_ids.mapped("ps_debit"))
        sum_end_credit_vnd      = sum(self.beta_line4_ids.mapped("end_credit"))
        sum_end_debit_vnd       = sum(self.beta_line4_ids.mapped("end_debit"))

        lines = []
        count = 1
        for data in self.beta_line4_ids:
            customer_name       = data.customer_name if data.customer_name else ""
            customer_code       = data.customer_code if data.customer_code else ""
            address             = data.address if data.address else ""
            vat                 = data.vat if data.vat else ""
            account_id          = data.account_id.code if data.account_id else ""
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
                "no"                : count,
                "customer_code"     : customer_code,
                "customer_name"     : customer_name,
                "address"           : address,
                "vat"               : vat,
                "account_id"        : account_id,
                "start_debit_usd"   : round(start_debit_usd, 2),
                "start_debit_vnd"   : round(start_debit_vnd),
                "start_credit_usd"  : round(start_credit_usd, 2),
                "start_credit_vnd"  : round(start_credit_vnd),
                "ps_debit_usd"      : round(ps_debit_usd, 2),
                "ps_debit_vnd"      : round(ps_debit_vnd),
                "ps_credit_usd"     : round(ps_credit_usd, 2),
                "ps_credit_vnd"     : round(ps_credit_vnd),
                "end_debit_usd"     : round(end_debit_usd, 2),
                "end_debit_vnd"     : round(end_debit_vnd),
                "end_credit_usd"    : round(end_credit_usd, 2),
                "end_credit_vnd"    : round(end_credit_vnd),
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_start_credit_vnd"  : f"{round(sum_start_credit_vnd):,}",
                "sum_start_debit_vnd"   : f"{round(sum_start_debit_vnd):,}",
                "sum_ps_credit_vnd"     : f"{round(sum_ps_credit_vnd):,}",
                "sum_ps_debit_vnd"      : f"{round(sum_ps_debit_vnd):,}",
                "sum_end_credit_vnd"    : f"{round(sum_end_credit_vnd):,}",
                "sum_end_debit_vnd"     : f"{round(sum_end_debit_vnd):,}",
                "sum_start_credit_usd"  : f"{round(sum_start_credit_usd, 2):,}",
                "sum_start_debit_usd"   : f"{round(sum_start_debit_usd, 2):,}",
                "sum_ps_credit_usd"     : f"{round(sum_ps_credit_usd, 2):,}",
                "sum_ps_debit_usd"      : f"{round(sum_ps_debit_usd, 2):,}",
                "sum_end_credit_usd"    : f"{round(sum_end_credit_usd, 2):,}",
                "sum_end_debit_usd"     : f"{round(sum_end_debit_usd, 2):,}",
            },
            "lines": lines,
        }

    def get_data_export_chi_tiet_cong_no_phai_tra_usd(self):
        sum_ps_credit_usd       = sum(self.beta_line5_ids.mapped("ps_credit_nt"))
        sum_ps_debit_usd        = sum(self.beta_line5_ids.mapped("ps_debit_nt"))
        sum_ps_credit_vnd       = sum(self.beta_line5_ids.mapped("ps_credit"))
        sum_ps_debit_vnd        = sum(self.beta_line5_ids.mapped("ps_debit"))

        lines = []
        count = 1
        for data in self.beta_line5_ids:
            move_id                 = data.move_id.display_name if data.move_id else ""
            date                    = data.date                 if data.date else ""
            invoice_date            = data.invoice_date         if data.invoice_date else ""
            reference               = data.reference            if data.reference else ""
            product_uom_quantity    = data.product_uom_quantity if data.product_uom_quantity else 0
            price_unit              = data.price_unit           if data.price_unit else 0
            note                    = data.note                 if data.note else ""
            uom_id                  = data.uom_id.display_name  if data.uom_id else ""
            account_id              = data.account_id.code      if data.account_id else ""
            account_dest_id         = data.account_dest_id.code if data.account_dest_id else ""
            ps_debit_usd            = data.ps_debit_nt
            ps_debit_vnd            = data.ps_debit
            ps_credit_usd           = data.ps_credit_nt
            ps_credit_vnd           = data.ps_credit
            end_debit_usd           = data.end_debit_nt
            end_debit_vnd           = data.end_debit
            end_credit_usd          = data.end_credit_nt
            end_credit_vnd          = data.end_credit
            vals = {
                "no"                  : count,
                "move_id"             : move_id,
                "date"                : date,
                "invoice_date"        : invoice_date,
                "reference"           : reference,
                "product_uom_quantity": product_uom_quantity,
                "price_unit"          : price_unit,
                "note"                : note,
                "uom_id"              : uom_id,
                "account_id"          : account_id,
                "account_dest_id"     : account_dest_id,
                "ps_debit_usd"        : round(ps_debit_usd, 2),
                "ps_debit_vnd"        : round(ps_debit_vnd),
                "ps_credit_usd"       : round(ps_credit_usd, 2),
                "ps_credit_vnd"       : round(ps_credit_vnd),
                "end_debit_usd"       : round(end_debit_usd, 2),
                "end_debit_vnd"       : round(end_debit_vnd),
                "end_credit_usd"      : round(end_credit_usd, 2),
                "end_credit_vnd"      : round(end_credit_vnd),
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_ps_credit_vnd"     : f"{round(sum_ps_credit_vnd):,}",
                "sum_ps_debit_vnd"      : f"{round(sum_ps_debit_vnd):,}",
                # "sum_end_credit_vnd"    : f"{round(sum_end_credit_vnd):,}",
                # "sum_end_debit_vnd"     : f"{round(sum_end_debit_vnd):,}",
                "sum_ps_credit_usd"     : f"{round(sum_ps_credit_usd, 2):,}",
                "sum_ps_debit_usd"      : f"{round(sum_ps_debit_usd, 2):,}",
                # "sum_end_credit_usd"    : f"{round(sum_end_credit_usd, 2):,}",
                # "sum_end_debit_usd"     : f"{round(sum_end_debit_usd, 2):,}",
            },
            "lines": lines,
        }

    def get_data_export_chi_tiet_cong_no_phai_thu_usd(self):
        sum_ps_credit_usd       = sum(self.beta_line6_ids.mapped("ps_credit_nt"))
        sum_ps_debit_usd        = sum(self.beta_line6_ids.mapped("ps_debit_nt"))
        sum_ps_credit_vnd       = sum(self.beta_line6_ids.mapped("ps_credit"))
        sum_ps_debit_vnd        = sum(self.beta_line6_ids.mapped("ps_debit"))

        lines = []
        count = 1
        for data in self.beta_line6_ids:
            move_id                 = data.move_id.display_name if data.move_id else ""
            date                    = data.date                 if data.date else ""
            invoice_date            = data.invoice_date         if data.invoice_date else ""
            reference               = data.reference            if data.reference else ""
            product_uom_quantity    = data.product_uom_quantity if data.product_uom_quantity else 0
            price_unit              = data.price_unit           if data.price_unit else 0
            note                    = data.note                 if data.note else ""
            default_code            = data.default_code         if data.default_code else ""
            account_id              = data.account_id.code      if data.account_id else ""
            account_dest_id         = data.account_dest_id.code if data.account_dest_id else ""
            ps_debit_usd            = data.ps_debit_nt
            ps_debit_vnd            = data.ps_debit
            ps_credit_usd           = data.ps_credit_nt
            ps_credit_vnd           = data.ps_credit
            end_debit_usd           = data.end_debit_nt
            end_debit_vnd           = data.end_debit
            end_credit_usd          = data.end_credit_nt
            end_credit_vnd          = data.end_credit
            vals = {
                "no"                  : count,
                "move_id"             : move_id,
                "date"                : date,
                "invoice_date"        : invoice_date,
                "reference"           : reference,
                "product_uom_quantity": product_uom_quantity,
                "price_unit"          : price_unit,
                "note"                : note,
                "default_code"        : default_code,
                "account_id"          : account_id,
                "account_dest_id"     : account_dest_id,
                "ps_debit_usd"        : round(ps_debit_usd, 2),
                "ps_debit_vnd"        : round(ps_debit_vnd),
                "ps_credit_usd"       : round(ps_credit_usd, 2),
                "ps_credit_vnd"       : round(ps_credit_vnd),
                "end_debit_usd"       : round(end_debit_usd, 2),
                "end_debit_vnd"       : round(end_debit_vnd),
                "end_credit_usd"      : round(end_credit_usd, 2),
                "end_credit_vnd"      : round(end_credit_vnd),
            }
            count += 1
            lines.append(vals)
        return {
            "sum": {
                "sum_ps_credit_vnd"     : f"{round(sum_ps_credit_vnd):,}",
                "sum_ps_debit_vnd"      : f"{round(sum_ps_debit_vnd):,}",
                # "sum_end_credit_vnd"    : f"{round(sum_end_credit_vnd):,}",
                # "sum_end_debit_vnd"     : f"{round(sum_end_debit_vnd):,}",
                "sum_ps_credit_usd"     : f"{round(sum_ps_credit_usd, 2):,}",
                "sum_ps_debit_usd"      : f"{round(sum_ps_debit_usd, 2):,}",
                # "sum_end_credit_usd"    : f"{round(sum_end_credit_usd, 2):,}",
                # "sum_end_debit_usd"     : f"{round(sum_end_debit_usd, 2):,}",
            },
            "lines": lines,
        }
