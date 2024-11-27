from odoo import models, fields, api
from datetime import datetime, timedelta

class UserIPHistory(models.Model):
    _name = 'user.ip.history'
    _description = 'Lịch sử địa chỉ IP người dùng'

    user_ip = fields.Char(string='Địa chỉ IP', required=True)
    timestamp = fields.Datetime(string='Thời gian', default=fields.Datetime.now)

    @api.model
    def create(self, vals):
        record = super(UserIPHistory, self).create(vals)
        self._update_ip_daily_count(record.user_ip)
        return record

    def _update_ip_daily_count(self, ip_address):
        today_start = datetime.combine(fields.Date.today(), datetime.min.time())
        today_end = today_start + timedelta(days=1)

        count = self.search_count([
            ('user_ip', '=', ip_address),
            ('timestamp', '>=', today_start),
            ('timestamp', '<', today_end)
        ])
        
        daily_ip = self.env['user.ip.history.daily'].search([
            ('user_ip', '=', ip_address),
            ('date', '=', fields.Date.today())
        ], limit=1)

        if daily_ip:
            daily_ip.write({'count': count})
        else:
            self.env['user.ip.history.daily'].create({
                'user_ip': ip_address,
                'date': fields.Date.today(),
                'count': count
            })

class UserIPHistoryDaily(models.Model):
    _name = 'user.ip.history.daily'
    _description = 'Tổng hợp số lần IP trong ngày'

    user_ip = fields.Char(string='Địa chỉ IP', required=True)
    date = fields.Date(string='Ngày', required=True)
    count = fields.Integer(string='Số lần xuất hiện', default=0)
