# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import requests
from datetime import datetime

from odoo import api, fields, models, _, _lt
from odoo.exceptions import UserError
import urllib.parse

from ..lib.const import get_date, get_timestamp, encode_token, decode_token, generate_random_string

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"
    
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Đơn bán hàng',
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Đính kèm',
    )

    public_url_add_image = fields.Char(string="Link thêm hình ảnh", compute="_compute_generate_public_url_add_image")
    
    api.depends('sale_order_id.state')
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