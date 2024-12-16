# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import requests
from datetime import datetime
import urllib.parse
from odoo import api, fields, models, _, _lt
from odoo.exceptions import UserError
from ..lib.const import get_date, get_timestamp, encode_token, decode_token, generate_random_string
from datetime import datetime

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

    ], string='Trạng thái sản xuất', store=True)
    
    state_delivery = fields.Selection(selection=[
        ('draft', 'Chưa sẵn sàng giao hàng'),
        ('confirm', 'Xác nhận giao hàng'),
        ('done', 'Hoàn thành'),
    ], string="Trạng thái giao hàng", readonly=True)

    sale_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Đính kèm',
        relation='sale_order_sale_attachment_rel',
        column1='sale_order_id',
        column2='attachment_id'
    )
    
    mrp_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Đính kèm',
        relation='sale_order_mrp_attachment_rel',
        column1='sale_order_id',
        column2='attachment_id'
    )

    otp_ids = fields.One2many(
        'otp.verification',
        'sale_order_id',
        string='OTP',
    )

    order_link_ids = fields.One2many(
        'order.link',
        'sale_order_id',
        string='Order Links'
    )


    public_url_cf_order = fields.Char(string="Link xác nhận đơn hàng", compute="_compute_generate_public_url_cf_order")
    public_url_cf_delivery = fields.Char(string="Link xác nhận giao hàng", compute="_compute_generate_public_url_cf_delivery")
    public_url_add_image = fields.Char(string="Link thêm hình ảnh", compute="_compute_generate_public_url_add_image")

    count_try_submit = fields.Integer('Số lần submit', default=0)

    # @api.depends('state')
    # def _compute_generate_public_url_cf_order(self):
    #     key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
    #     text = "%s | %s | %s | %s" % (get_timestamp(), generate_random_string(20), self._name, self.id)
    #     text = "%s | %s | %s" % (get_timestamp(), generate_random_string(20), self.id)
    #     token = encode_token(text, key)
    #     url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
    #     for order in self:
    #         if order.state in ['draft', 'sent']:
    #             order.state = 'sent'
    #             order.public_url_cf_order = "%s/public/order/confirm-order?token=%s" % (url, urllib.parse.quote(token))
    #         else:
    #             order.public_url_cf_order = ""

    # @api.depends('state', 'state_delivery', 'state_mrp')
    # def _compute_generate_public_url_cf_delivery(self):
    #     key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
    #     text = "%s | %s | %s" % (get_timestamp(), generate_random_string(20), self.id)
    #     token = encode_token(text, key)
    #     url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
    #     for order in self:
    #         if order.state == 'sale' and order.state_delivery == 'ready' and order.state_mrp == 'done':
    #             order.public_url_cf_delivery = "%s/public/order/confirm-delivery?token=%s" % (url, urllib.parse.quote(token))
    #         else:
    #             order.public_url_cf_delivery = ""

    # @api.depends('state')
    # def _compute_generate_public_url_add_image(self):
    #     key = self.env["ir.config_parameter"].sudo().get_param("confirm_order_process.serect_key_public_user", False)
    #     text = "%s | %s | %s | %s" % (get_timestamp(), generate_random_string(20), self._name, self.id)
    #     token = encode_token(text, key)
    #     url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", False)
    #     for order in self:
    #         if order.state in ['sale', 'done']:
    #             order.public_url_add_image = "%s/public/upload_files_to_order?token=%s" % (url, urllib.parse.quote(token))
    #         else:
    #             order.public_url_add_image = ""

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        for order in res:
            link_type = None
            if order.state in ['draft', 'sent']:
                link_type = 'order'
            elif order.state == 'sale' and order.state_delivery == 'draft' and order.state_mrp == 'done':
                link_type = 'delivery'
            if link_type:
                order_link_ids = order.order_link_ids.filtered(lambda l: l.expired_date < datetime.now() and l.type == link_type and l.state == 'draft')
                if not order_link_ids:
                    order.write({
                        'order_link_ids': [(0, 0, {
                            'sale_order_id': order.id,
                            "name": order.name,
                            'type': link_type,
                        })]
                    })
            if order.state == 'sale' and order.state_delivery in ('draft', 'confirm') and order.state_mrp == 'done':
                link_type = 'image'
                order_link_ids = order.order_link_ids.filtered(lambda l: l.expired_date < datetime.now() and l.type == link_type and l.state == 'draft')
                if not order_link_ids:
                    order.write({
                        'order_link_ids': [(0, 0, {
                            'sale_order_id': order.id,
                            "name": order.name,
                            'type': link_type,
                        })]
                    })
        return res

        
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for order in self:
            link_type = None
            if ('state' in vals) or ('state_delivery' in vals) or ('state_mrp' in vals):
                if order.state in ['draft', 'sent']:
                    link_type = 'order'
                elif order.state == 'sale' and order.state_delivery == 'draft' and order.state_mrp == 'done':
                    link_type = 'delivery'
                if link_type:
                    order_link_ids = order.order_link_ids.filtered(lambda l: l.expired_date < datetime.now() and l.type == link_type and l.state == 'draft')
                    if not order_link_ids:
                        order.write({
                            'order_link_ids' : [(0,0,{
                                'sale_order_id': order.id,
                                "name": order.name,
                                'type': link_type,
                            })]
                        })
                if order.state == 'sale' and order.state_delivery in ('draft', 'confirm') and order.state_mrp == 'done':
                    link_type = 'image'
                    order_link_ids = order.order_link_ids.filtered(lambda l: l.expired_date < datetime.now() and l.type == link_type and l.state == 'draft')
                    if not order_link_ids:
                        order.write({
                            'order_link_ids' : [(0,0,{
                                'sale_order_id': order.id,
                                "name": order.name,
                                'type': link_type,
                            })]
                        })
        return res


    @api.depends('order_link_ids')
    def _compute_generate_public_url_cf_order(self):
        for order in self:
            link = order.order_link_ids.filtered(lambda l: l.type == 'order' and l.state == 'draft')
            if link:
                order.public_url_cf_order = link[0].url
            else:
                order.public_url_cf_order = ""

    @api.depends('order_link_ids')
    def _compute_generate_public_url_cf_delivery(self):
        for order in self:
            link = order.order_link_ids.filtered(lambda l: l.type == 'delivery' and l.state == 'draft')
            if link:
                order.public_url_cf_delivery = link[0].url
            else:
                order.public_url_cf_delivery = ""

    @api.depends('order_link_ids')
    def _compute_generate_public_url_add_image(self):
        for order in self:
            link = order.order_link_ids.filtered(lambda l: l.type == 'image' and l.state == 'draft')
            if link:
                order.public_url_add_image = link[0].url
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


    def action_reset_public_url(self):
        for order in self:
            for link in order.order_link_ids.filtered(lambda l: l.state == 'draft'):
                order.write({
                    'order_link_ids': [(0, 0, {
                        'sale_order_id': order.id,
                        "name": order.name,
                        'type': link.type,
                        'url': link._generate_order_url(order),
                    })]
                })
        return



    ####################################
    
    def action_resend_otp(self):
        self.otp_ids.filtered(lambda l:l.state=='unverified').action_send_email()

    def public_confirm(self, otp_id):
        for order in self:
            if order.state in ['draft', 'sent']:
                order.action_confirm()
                order.state_delivery = 'draft'
                if otp_id:
                    otp_id.write({'state': 'verified'})
                order.order_link_ids.filtered(lambda l: l.type=='order' and l.state=='draft').write({'state':'consume'})
            elif order.state in ['sale']:
                order.action_confirm_delivery()
                if otp_id:
                    otp_id.write({'state': 'verified'})
    
    def action_confirm_delivery(self):
        for order in self:
            order.state_delivery = 'confirm'
            order.order_link_ids.filtered(lambda l: l.type=='delivery' and l.state=='draft').write({'state':'consume'})

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
