from odoo.tools.profiler import QwebTracker
from markupsafe import Markup, escape
from odoo import models, fields, api, _
from odoo.tools import config, safe_eval, pycompat, SUPPORTED_DEBUGGER
import logging

_logger = logging.getLogger(__name__)

T_CALL_SLOT = '0'

class IrQweb(models.AbstractModel):
    _inherit = 'ir.qweb'

    @QwebTracker.wrap_render
    @api.model
    def _render(self, template, values=None, **options):
        values = values.copy() if values else {}
        if T_CALL_SLOT in values:
            raise ValueError(f'values[{T_CALL_SLOT}] should be unset when call the _render method and only set into the template.')

        irQweb = self.with_context(**options)._prepare_environment(values)

        safe_eval.check_values(values)

        template_functions, def_name = irQweb._compile(template)
        render_template = template_functions[def_name]
        rendering = render_template(irQweb, values)
        result = ''.join([item if item is not None else '' for item in rendering])

        return Markup(result)