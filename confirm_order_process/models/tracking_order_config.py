from odoo import models, fields, api

class tracking_order_config(models.Model):
    _name = "tracking.order.config"

    name = fields.Char(string="Tên")
    src_location = fields.Many2one('res.partner', string='Địa chỉ mặc định')
    src_latitude = fields.Float(string='Vĩ độ mặc định', related='src_location.partner_latitude')
    src_longitude = fields.Float(string='Kinh độ mặc định', related='src_location.partner_longitude')

    
