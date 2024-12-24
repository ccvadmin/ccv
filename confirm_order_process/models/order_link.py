from odoo import models, fields, api
import urllib.parse
from datetime import datetime
from ..const import get_date, get_timestamp, encode_token, decode_token, generate_random_string
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class OrderLink(models.Model):
    _name = 'order.link'
    _description = 'Order Link for MRP Production and Sale Order'

    name = fields.Char(string='Tên')
    url = fields.Char(string='Đường dẫn')
    type = fields.Selection(selection=[
        ('order', 'Xác nhận đơn hàng'),
        ('delivery', 'Xác nhận giao hàng'),
        ('image', 'Thêm hình ảnh'),
        ('driver', 'Tài xế'),
        ('follower', 'Theo dõi giao hàng'),
    ], string="Loại đường dẫn")
    state = fields.Selection(selection=[
        ('draft', 'Mới'),
        ('consume', 'Đã sử dụng'),
        ('expired', 'Hết hạn'),
    ], string="Trạng thái đường dẫn", default='draft')

    sale_order_id = fields.Many2one('sale.order', string='Đơn bán hàng', store=True)
    location_id = fields.Many2one('sales.order.location', string='Vị trí xe', store=True)
    has_location = fields.Boolean(compute='_compute_location')
    sale_order_name = fields.Char(related='sale_order_id.name', string='Đơn bán hàng', readonly=True, store=True)
    expired_date = fields.Datetime(string="Ngày hết hạn")
    vehicle_number = fields.Char(string="Số xe",related='location_id.vehicle_number')

    @api.depends('location_id')
    def _compute_location(self):
        for record in self:
            record.has_location = record.location_id is not False

    @api.model_create_multi
    def create(self, val_lists):
        vals = []
        for val in val_lists:
            if not val.get('expired_date', False):
                now = datetime.now()
                end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)
                val.update({'expired_date': end_of_day})

            if val.get('sale_order_id', False):
                if val.get('type') != 'driver' and val.get('type') != 'follower':
                    existing_links = self.search([
                        ('sale_order_id', '=', val.get('sale_order_id')),
                        ('type', '=', val.get('type')),
                        ('state', '=', 'draft'),
                    ])
                    if existing_links:
                        existing_links.write({'state': 'expired'})
            vals.append(val)
        records = super(OrderLink, self).create(vals)
        
        for record in records:
            for val in vals:
                if record.sale_order_id.id == val.get('sale_order_id', False):
                    if not val.get('url', False):
                        if record.type == 'order':
                            record.url = record._generate_order_url(record.sale_order_id)
                        elif record.type == 'delivery':
                            record.url = record._generate_delivery_url(record.sale_order_id)
                        elif record.type == 'image':
                            record.url = record._generate_image_url(record.sale_order_id)
                        elif record.type == 'driver':
                            record.url = record._generate_tracking_url(record.sale_order_id,role='driver')
                        elif record.type == 'follower':
                            record.url = record._generate_tracking_url(record.sale_order_id,role='follower')
                    else:
                        record.url = val.get('url', False)
                    break
        return records

    def action_open_location(self):
        if not self.location_id:
            raise UserError('Chưa có địa chỉ cho xe!!!')
        return {
            "type": "ir.actions.act_window",
            "res_model": "sales.order.location",
            "views": [[False, "form"]],
            "res_id": self.location_id.id,
            "target": "current",
        }

    def action_expired_link(self):
        self.write({'state': 'expired'})

    def reset_serect_key(self):
        self.env['ir.config_parameter'].sudo().set_param('confirm_order_process.serect_key_public_user', generate_random_string(150))

    def _generate_order_url(self, order):
        key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        if not key:
            self.reset_serect_key()
            key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        text = "%s | %s | %s" % (get_timestamp(), generate_random_string(20), order.id)
        token = encode_token(text, key)
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
        return "%s/public/order/confirm-order?token=%s" % (base_url, urllib.parse.quote(token))

    def _generate_delivery_url(self, order):
        key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        if not key:
            self.reset_serect_key()
            key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        text = "%s | %s | %s" % (get_timestamp(), generate_random_string(20), order.id)
        token = encode_token(text, key)
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
        return "%s/public/order/confirm-delivery?token=%s" % (base_url, urllib.parse.quote(token))

    def _generate_image_url(self, order):
        key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        if not key:
            self.reset_serect_key()
            key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        text = "%s | %s | %s" % (get_timestamp(), generate_random_string(20), order.id)
        token = encode_token(text, key)
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
        return "%s/public/upload_files_to_order?token=%s" % (base_url, urllib.parse.quote(token))

    def _generate_tracking_url(self, order, role='driver'):
        key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.image_key_public_user", False)
        if not key:
            self.env['ir.config_parameter'].sudo().set_param('confirm_order_process.image_key_public_user', generate_random_string(150))
            key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.image_key_public_user", False)
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
        if not self.location_id and role == 'role':
            raise UserError("URL chưa gắn với tài xế")
        id = self.location_id.id if self.location_id else order.id
        model = 'sales.order'
        text = '%s | %s | %s | %s | %s' % (get_timestamp(), generate_random_string(20), role, model, id)
        token = encode_token(text, key)
        return "%s/public/order/track-journey?token=%s&role=%s&model=%s&id=%s" % (base_url, urllib.parse.quote(token),role,model,id)
