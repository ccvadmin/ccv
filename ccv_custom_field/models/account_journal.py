from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    ccv_restrict_mode_hash_table = fields.Boolean(default=False)
