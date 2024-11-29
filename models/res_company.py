# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

import base64
class ResCompany(models.Model):
    _inherit = "res.company"
    
    ngrok_url = fields.Char('NGROK URL')

    def test_action(self):
        sale = self.env['sale.order'].browse(180)
        for order in sale:
            pdf, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf('sale.action_report_saleorder', order.ids)
            datas = base64.encodebytes(pdf)


            # Create an attachment
            self.env['ir.attachment'].create({
                'name': f'{order.name}-2.pdf',
                'type': 'binary',
                'datas': datas,
                'res_model': 'sale.order',
                'res_id': order.id,
                'mimetype': 'application/pdf',
            })