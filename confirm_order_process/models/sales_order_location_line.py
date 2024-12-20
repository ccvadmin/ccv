from odoo import models, fields, api

class SalesOrderLocationLine(models.Model):
    _name = "sales.order.location.line"
    _description = "Sales Order Location Line"
    
    location_id = fields.Many2one('sales.order.location', string="Sales Order Location", required=True)
    
    latitude = fields.Float(string="Vĩ độ", required=True)
    longitude = fields.Float(string="Kinh độ", required=True)

    date = fields.Datetime(string="Thời gian")
    
