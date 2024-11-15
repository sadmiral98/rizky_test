# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

class ResCompany(models.Model):
    _inherit = "res.company"
    
    ngrok_url = fields.Char('NGROK URL')