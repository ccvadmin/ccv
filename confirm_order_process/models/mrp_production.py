# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import requests
from datetime import datetime

from odoo import api, fields, models, _, _lt
from odoo.exceptions import UserError

import random
import string

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
    