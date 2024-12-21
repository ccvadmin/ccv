from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class UserIPHistory(models.Model):
    _name = 'user.ip.history'
    _description = 'Lịch sử địa chỉ IP người dùng'

    name = fields.Char(string='Địa chỉ IP', required=True, readonly=True)
    timestamp = fields.Datetime(string='Thời gian', default=fields.Datetime.now, readonly=True)

    @api.model
    def create(self, vals):
        record = super(UserIPHistory, self).create(vals)
        self._update_ip_daily_count(record.name)
        return record

    def _update_ip_daily_count(self, ip_address):
        today_start = datetime.combine(fields.Date.today(), datetime.min.time())
        today_end = today_start + timedelta(days=1)

        count = self.search_count([
            ('name', '=', ip_address),
            ('timestamp', '>=', today_start),
            ('timestamp', '<', today_end)
        ])
        
        daily_ip = self.env['user.ip.history.daily'].search([
            ('name', '=', ip_address),
            ('date', '=', fields.Date.today())
        ], limit=1)

        if daily_ip:
            daily_ip.write({'count': count})
        else:
            self.env['user.ip.history.daily'].create({
                'name': ip_address,
                'date': fields.Date.today(),
                'count': count
            })

class UserIPHistoryDaily(models.Model):
    _name = 'user.ip.history.daily'
    _description = 'Tổng hợp số lần IP trong ngày'

    name = fields.Char(string='Địa chỉ IP', required=True, readonly=True)
    date = fields.Date(string='Ngày', required=True, readonly=True)
    count = fields.Integer(string='Số lần xuất hiện', default=0, readonly=True)

    def action_show_history(self):
        start = datetime.combine(self.date, datetime.min.time())
        end = datetime.combine(self.date, datetime.max.time())
        return {
            "type": "ir.actions.act_window",
            "res_model": "user.ip.history",
            "name": "[%s] Lịch sử truy cập ngày %s" % ((self.name if self.name else ""), self.date),
            "views": [[False, "tree"]],
            "domain": [
                ('name', '=', self.name),
                ('timestamp', '>=', start),
                ('timestamp', '<', end)
            ],
            "target": "current",
        }
