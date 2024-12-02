from odoo import models, fields, api
import logging
from datetime import datetime
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    @api.model
    def convert_money(self, amount):
        units = ['', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín']
        tens = ['', 'mười', 'hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
        thousands = ['', 'nghìn', 'triệu', 'tỷ']

        try:
            cur_amount = int(float(amount))
        except ValueError:
            return ""

        def number_to_text(num):
            if num == 0:
                return 'không'
            
            num = str(num)
            length = len(num)
            result = []
            
            groups = [num[max(0, length - 3*(i+1)): length - 3*i] for i in range((length // 3) + 1)]
            groups.reverse()
            
            for idx, group in enumerate(groups):
                n = int(group)
                group_result = []
                
                if n >= 100:
                    group_result.append(units[n // 100] + " trăm")
                    n %= 100
                if n >= 20:
                    group_result.append(tens[n // 10])
                    n %= 10
                elif n >= 10:
                    group_result.append('mười')
                    n %= 10
                if n > 0:
                    group_result.append(units[n])
                
                if group_result:
                    result.append(" ".join(group_result) + " " + thousands[len(groups) - idx - 1])
            
            return " ".join(result).strip()
        
        label = number_to_text(cur_amount).strip()

        return label[:1].upper() + label[1:].lower()

    @api.model
    def convert_vnd(self, amount):
        return f"{amount:,.0f}"

    @api.model
    def convert_date(self, date):
        if date:
            return fields.Date.to_string(date)
        return ''

    @api.model
    def convert_print(self, date_value):
        if not date_value:
            return ""
        if isinstance(date_value, datetime):
            date_value = date_value.date()
        if isinstance(date_value, fields.Date):
            date_value = datetime.strptime(str(date_value), '%Y-%m-%d').date()
        return date_value.strftime('%d/%m/%Y')

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

    def get_convert_money_total_amount(self):
        return self.convert_money(self.total_amount)
