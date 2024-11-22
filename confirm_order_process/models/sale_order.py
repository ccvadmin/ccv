# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import requests
from datetime import datetime
import urllib.parse
from odoo import api, fields, models, _, _lt
from odoo.exceptions import UserError
from ..lib.const import get_date, get_timestamp, encode_token, decode_token, generate_random_string

import random
import string

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    state_mrp = fields.Selection(selection=[
        ('draft', 'Chưa sản xuất'),
        ('progress', 'Đang sản xuất'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Hủy')

    ], string='Trạng thái sản xuất', compute="_compute_state_mrp")
    
    state_delivery = fields.Selection(selection=[
        ('draft', 'Chưa sẵn sàng giao hàng'),
        ('sent', 'Đã gửi thông tin xác nhận giao nhận'),
        ('confirm', 'Xác nhận giao hàng'),
        ('done', 'Hoàn thành'),
    ], string="Trạng thái giao hàng", readonly=True)

    mrp_production_ids = fields.One2many(
        'mrp.production',
        'sale_order_id',
        string='Lệnh sản xuất',
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Đính kèm',
    )

    otp_ids = fields.One2many(
        'otp.verification',
        'sale_order_id',
        string='OTP',
    )

    public_url_cf_order = fields.Char(string="Link xác nhận đơn hàng", compute="_compute_generate_public_url_cf_order")
    public_url_cf_delivery = fields.Char(string="Link xác nhận giao hàng", compute="_compute_generate_public_url_cf_delivery")
    public_url_add_image = fields.Char(string="Link thêm hình ảnh", compute="_compute_generate_public_url_add_image")

    count_try_submit = fields.Integer('Số lần submit', default=0)

    @api.depends("mrp_production_ids")
    def _compute_state_mrp(self):
        for order in self:
            state_list = order.mrp_production_ids.mapped('state')
            if any([state for state in state_list if state in ["draft", "confirmed"]]):
                order.state_mrp = 'draft'
            elif any([state for state in state_list if state in ["progress", "to_close"]]):
                order.state_mrp = 'progress'
            elif any([state for state in state_list if state in ["cancel"]]):
                order.state_mrp = 'cancel'
            elif any([state for state in state_list if state in ["done"]]):
                order.state_mrp = 'done'
            else:
                order.state_mrp = ''

    @api.depends('state')
    def _compute_generate_public_url_cf_order(self):
        key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        text = "%s | %s | %s | %s" % (get_timestamp(), generate_random_string(20), self._name, self.id)
        text = "%s | %s | %s" % (get_timestamp(), generate_random_string(20), self.id)
        token = encode_token(text, key)
        url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
        for order in self:
            if order.state in ['draft', 'sent']:
                order.state = 'sent'
                order.public_url_cf_order = "%s/public/order/confirm-order?token=%s" % (url, urllib.parse.quote(token))
            else:
                order.public_url_cf_order = ""

    @api.depends('state', 'state_delivery', 'state_mrp')
    def _compute_generate_public_url_cf_delivery(self):
        key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        text = "%s | %s | %s" % (get_timestamp(), generate_random_string(20), self.id)
        token = encode_token(text, key)
        url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
        for order in self:
            if order.state == 'sale' and order.state_delivery == 'ready' and order.state_mrp == 'done':
                order.public_url_cf_delivery = "%s/public/order/confirm-delivery?token=%s" % (url, urllib.parse.quote(token))
            else:
                order.public_url_cf_delivery = ""

    @api.depends('state')
    def _compute_generate_public_url_add_image(self):
        key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
        text = "%s | %s | %s | %s" % (get_timestamp(), generate_random_string(20), self._name, self.id)
        token = encode_token(text, key)
        url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
        for order in self:
            if order.state in ['sale', 'done']:
                order.public_url_add_image = "%s/public/upload_files_to_order?token=%s" % (url, urllib.parse.quote(token))
            else:
                order.public_url_add_image = ""


    ####################################
    # TODO: Chuyển 2 hàm button tích hợp ZALO
    # TODO: Tạo form SMS
    # TODO: Tích hợp tạo OTP gửi SMS
    # Các đường link đã hoàn done, có thể hoạt động
    # Serect key là được reset vào 00:00 hàng ngày
    # Các giao dịch chỉ được thực hiện trong ngày, nếu sang ngày hôm sau phải gửi lại đường link
    ####################################

    def test_btn(self):
        raise UserError(self.public_url)
    
    def test_btn1(self):
        self.state_delivery = 'sent'
        raise UserError(self.public_url)

    ####################################
    
    def action_resend_otp(self):
        self.otp_ids.filtered(lambda l:l.state=='unverified').action_send_email()

    def public_confirm(self, otp_id):
        if self.state in ['draft', 'sent']:
            self.action_confirm()
            self.state_delivery = 'draft'
            if otp_id:
                otp_id.write({'state': 'verified'})
        elif self.state in ['sale']:
            self.action_confirm_delivery()
            if otp_id:
                otp_id.write({'state': 'verified'})
    
    def action_confirm_delivery(self):
        self.state_delivery = 'confirm'

    def action_done_delivery(self):
        self.state_delivery = 'done'
        self.state = 'done'

    def send_message_w_trigger(self, type='order'):
        for order in self:
            msg = ""
            if order.user_id and order.user_id.partner_id:
                if type == "order":
                    msg = f"Đơn {order.name} xác nhận thành công!"
                elif type == 'delivery':
                    msg = f"Đơn {order.name} xác nhận giao hàng thành công!"
                channel = self.env['mail.channel'].search([
                    ('name', '=', 'Confirm Order')
                ]).filtered(lambda l:order.user_id.partner_id.id in l.channel_member_ids.partner_id.ids)

                if not channel:
                    channel = self.env['mail.channel'].create({
                        'name': 'Confirm Order',
                    })
                    _logger.info(order.user_id.partner_id.id)
                    channel.add_members(partner_ids=[order.user_id.partner_id.id])

                message = self.env['mail.message'].create({
                    'subject': 'Đơn %s đã được cập nhật' % (order.name),
                    'body':  "%s\nBạn có thể xem chi tiết <a href='/web#id=%s&model=sale.order&view_type=form'>TẠI ĐÂY</a>." % (msg, order.id),
                    'message_type': 'auto_comment',
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                    'model': 'mail.channel',
                    'res_id': channel[0].id,
                })
