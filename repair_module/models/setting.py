# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    faulty_location_id = fields.Many2one('stock.location', string="Faulty Product Location")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            faulty_location_id=int(self.env["ir.config_parameter"]
                .sudo()
                .get_param("faulty_location_id"))
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "faulty_location_id", self.faulty_location_id.id
        )
