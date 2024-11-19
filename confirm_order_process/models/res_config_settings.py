# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import requests
from datetime import datetime

from odoo import api, fields, models, _, _lt
from odoo.exceptions import UserError

from ..lib.const import generate_random_string

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    def reset_serect_key(self):
        self.env['ir.config_parameter'].set_param('confirm_order_process.serect_key_public_user', generate_random_string(150))
        return True
