# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import requests
from datetime import datetime
import urllib.parse
from odoo import api, fields, models, _, _lt, SUPERUSER_ID
from odoo.exceptions import UserError
from ..const import get_date, get_timestamp, encode_token, decode_token, generate_random_string
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

    order_link_driver_ids = fields.One2many(
        'order.link',
        'sale_order_id',
        string='Driver Links',
        readonly=True,
        store=False,
        compute="_compute_order_link",
    )

    ####################################
    # TODO: Tích hợp ZALO gửi các đường link bên dưới
    # Các đường link đã done, có thể hoạt động
    # Serect key là được reset vào 00:00 hàng ngày
    # Các giao dịch chỉ được thực hiện trong ngày, nếu sang ngày hôm sau phải gửi lại đường link
    ####################################

    public_url_cf_order = fields.Char(string="Link xác nhận đơn hàng", compute="_compute_order_link")
    public_url_cf_delivery = fields.Char(string="Link xác nhận giao hàng", compute="_compute_order_link")
    public_url_add_image = fields.Char(string="Link thêm hình ảnh", compute="_compute_order_link")
    public_url_tracking_order = fields.Char(string="Link theo dõi giao hàng", compute="_compute_order_link")
    number_of_vehicles = fields.Integer(string="Số lượng xe", default=1)

    count_try_submit = fields.Integer('Số lần submit', default=0)

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
            if order.order_link_driver_ids:
                link_type = 'follower'
                order.write({
                    'order_link_ids' : [(0,0,{
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
            if 'order_link_driver_ids' in vals and order.order_link_driver_ids:
                link_type = 'follower'
                order.write({
                    'order_link_ids' : [(0,0,{
                        'sale_order_id': order.id,
                        "name": order.name,
                        'type': link_type,
                    })]
                })
        return res

    @api.depends('order_link_ids')
    def _compute_order_link(self):
        url_fields = {
            'order': 'public_url_cf_order',
            'delivery': 'public_url_cf_delivery',
            'image': 'public_url_add_image',
            'follower': 'public_url_tracking_order',
        }
        for order in self:
            for link_type, field_name in url_fields.items():
                link = order.order_link_ids.filtered(lambda l: l.type == link_type and l.state == 'draft')
                setattr(order, field_name, link[0].url if link else "")
            order_link = self.env['order.link']
            if order.order_link_ids:
                order_link = order.order_link_ids.filtered(lambda l: l.type == 'driver')
            order.order_link_driver_ids = order_link

    def action_reset_public_url(self):
        for order in self:
            types = ('delivery','image','order','follower')
            order_link_ids = order.order_link_ids.filtered(lambda l: l.type in types and l.state == 'draft')
            order_link_ids.write({'state': 'expired'})
            link_type = None
            if order.state in ['draft', 'sent']:
                link_type = 'order'
            elif order.state == 'sale' and order.state_delivery == 'draft' and order.state_mrp == 'done':
                link_type = 'delivery'
            if link_type:
                order.write({
                    'order_link_ids' : [(0,0,{
                        'sale_order_id': order.id,
                        "name": order.name,
                        'type': link_type,
                    })]
                })
            if order.state == 'sale' and order.state_delivery in ('draft', 'confirm') and order.state_mrp == 'done':
                link_type = 'image'
                order.write({
                    'order_link_ids' : [(0,0,{
                        'sale_order_id': order.id,
                        "name": order.name,
                        'type': link_type,
                    })]
                })
            if order.order_link_driver_ids.filtered(lambda l: l.state == 'draft'):
                link_type = 'follower'
                order.write({
                    'order_link_ids' : [(0,0,{
                        'sale_order_id': order.id,
                        "name": order.name,
                        'type': link_type,
                    })]
                })
        return
    
    def action_create_public_driver_url(self):
        for order in self:
            order_links = []
            size = order.number_of_vehicles - len(order.order_link_ids.filtered(lambda l:l.type == 'driver' and l.state == 'draft'))
            if order.number_of_vehicles <= 0:
                raise UserError('Số lượng xe không đúng!!!')
            if size <= 0:
                raise UserError('Số lượng đường link đã đủ!!!')
            partner_id = order.partner_id
            if partner_id.partner_latitude == 0 or partner_id.partner_longitude == 0:
                raise UserError('Khách hàng chưa được xác định tọa độ bằng địa chỉ!!!')
            for i in range(size):
                location = self.env['sales.order.location'].create({
                    'order_id': order.id,
                    'name': f"Vị trí cho đơn {order.name} - Xe {i+1}"
                })
                order_links.append((0, 0, {
                    'sale_order_id': order.id,
                    'name': order.name,
                    'type': 'driver',
                    'location_id': location.id
                }))
            if order_links:
                order.write({
                    'order_link_ids': order_links,
                })
        return

    def action_resend_otp(self):
        self.otp_ids.filtered(lambda l:l.state=='unverified').action_send_sms()

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.env.su:
            self = self.with_user(SUPERUSER_ID)
        for order in self:
            order.state_delivery = 'draft'
        return res

    def public_confirm(self, otp_id):
        for order in self:
            if order.state in ['draft', 'sent']:
                order.action_confirm()
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
            order.order_link_ids.filtered(lambda l: l.state=='draft').write({'state':'consume'})

    def send_message_w_trigger(self, type='order'):
        channel_env = self.env['mail.channel'].sudo()
        mail_env = self.env['mail.message'].sudo()
        this = self.sudo()
        for order in this.sudo():
            msg = ""
            if order.user_id:
                list_partner = []
                if order.user_id.partner_id:
                    list_partner.append(order.user_id.partner_id.id)
                else:
                    continue
                if order.sales_assistant_ids:
                    list_partner += order.sales_assistant_ids.mapped('partner_id').mapped('id')
                if order.sales_team_captain_id:
                    if order.sales_team_captain_id.partner_id:
                        list_partner.append(order.sales_team_captain_id.partner_id.id)
                if type == "order":
                    msg = f"Đơn {order.name} xác nhận thành công!"
                elif type == 'delivery':
                    msg = f"Đơn {order.name} xác nhận giao hàng thành công!"
                channel = channel_env.search([('name', '=', 'Confirm Order')]).filtered(lambda l:order.user_id.partner_id.id in l.channel_member_ids.partner_id.ids)

                if not channel:
                    channel = channel_env.create({'name': 'Confirm Order',})
                    channel.add_members(partner_ids=list_partner)

                message = mail_env.create({
                    'subject': 'Đơn %s đã được cập nhật' % (order.name),
                    'body':  "%s\nBạn có thể xem chi tiết <a href='/web#id=%s&model=sale.order&view_type=form'>TẠI ĐÂY</a>." % (msg, order.id),
                    'message_type': 'auto_comment',
                    'subtype_id': this.env.ref('mail.mt_comment').id,
                    'model': 'mail.channel',
                    'res_id': channel[0].id,
                })
