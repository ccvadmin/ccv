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
        domain="[('state','!=','done')]",
        store=True,
    )
    
    @api.depends(
        'move_raw_ids.state', 'move_raw_ids.quantity_done', 'move_finished_ids.state',
        'workorder_ids.state', 'product_qty', 'qty_producing', 'sale_order_id')
    def _compute_state(self):
        super(MrpProduction, self)._compute_state()
        for mrp in self:
            productions = self.env['mrp.production'].search([('sale_order_id', '=', mrp.sale_order_id.id)])
            state_list = productions.mapped('state')
            if any([state for state in state_list if state in ["draft", "confirmed"]]):
                mrp.sale_order_id.state_mrp = 'draft'
            elif any([state for state in state_list if state in ["progress", "to_close"]]):
                mrp.sale_order_id.state_mrp = 'progress'
            elif any([state for state in state_list if state in ["cancel"]]):
                mrp.sale_order_id.state_mrp = 'cancel'
            elif any([state for state in state_list if state in ["done"]]):
                mrp.sale_order_id.state_mrp = 'done'
            else:
                mrp.sale_order_id.state_mrp = ''