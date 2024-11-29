from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    restrict_mode_hash_table = fields.Boolean(
        related="journal_id.ccv_restrict_mode_hash_table"
    )

    def button_draft(self):
        super(AccountMove, self).button_draft()
        self.write({"posted_before": False})
