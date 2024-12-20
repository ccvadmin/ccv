from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SalesOrderLocation(models.Model):
    _name = "sales.order.location"
    _description = "Sales Order Location"

    name = fields.Char(string="Tên")
    order_id = fields.Many2one('sale.order', string="Đơn bán hàng", required=True)
    url = fields.Char(string="Link", compute="_compute_link")

    latitude = fields.Float(string="Vĩ độ", compute="_compute_location", store=True)
    longitude = fields.Float(string="Kinh độ", compute="_compute_location", store=True)

    vehicle_number = fields.Char(string="Số xe")

    line_ids = fields.One2many('sales.order.location.line', 'location_id', string="Location Lines")

    def name_get(self):
        result = []
        for rec in self.sudo():
            name = "Vị trí "
            if rec.order_id and rec.vehicle_number:
                name += f" xe {rec.vehicle_number}"
            name += f" cho đơn hàng {rec.order_id.name}"
            result.append((rec.id, name))
        return result

    @api.depends('line_ids.latitude', 'line_ids.longitude')
    def _compute_location(self):
        for record in self:
            line = record.line_ids.filtered(lambda l: l.date == max(record.line_ids.mapped('date')))
            if line:
                record.latitude = line.latitude
                record.longitude = line.longitude
            else:
                record.latitude = 0
                record.longitude = 0
    
    @api.depends('order_id')
    def _compute_link(self):
        for record in self:
            link = self.env['order.link'].search([('location_id','=',int(record.id))])
            _logger.info(link)
            record.url = link.url
            _logger.info(record.url)


