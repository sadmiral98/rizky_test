# -*- coding: utf-8 -*-
# Copyright 2022 IZI PT Solusi Usaha Mudah
import random, json
from odoo import http, fields
from datetime import datetime, timedelta
from odoo.http import request
import requests
from bs4 import BeautifulSoup
import logging
_logger = logging.getLogger('dke.iziapp.id')
from odoo.addons.whatsapp.controller.main import Webhook
from odoo.addons.whatsapp.tools.whatsapp_api import WhatsAppApi

class WhatsAppApiInherit(WhatsAppApi):
    def _send_whatsapp(self, number, message_type, send_vals, parent_message_id=False):
            _logger.info("\n\ndke.iziapp.id : POST Send Whatsapp disabling the function!")

        # data = {
        #     'number':number,
        #     'message_type':message_type,
        #     'send_vals':send_vals,
        #     'parent_message_id':parent_message_id
        # }
        # json_data = json.dumps(data)
        # if request.env.company.ngrok_url:
        #     _logger.info("\n\ndke.iziapp.id : POST Send Whatsapp : ngrok url found!")
        #     url = f"{request.env.company.ngrok_url}testsendwhatsapp"
        #     response = requests.post(url, json=json_data)
        # else:
        #     _logger.info("\n\ndke.iziapp.id : POST Send Whatsapp : ngrok url NOT found!")
        # super()._send_whatsapp(number, message_type, send_vals, parent_message_id)
class WebController(Webhook):
    @http.route()
    def webhookpost(self):
        data = json.loads(request.httprequest.data)
        
        # _logger.info("\n\ndke.iziapp.id : Webhook Data: %s", json.dumps(data, indent=4))
        _logger.info("\n\ndke.iziapp.id : req :",request.env.company.id)
        _logger.info("\n\ndke.iziapp.id : req :",request.env.company.name)
        _logger.info("\n\ndke.iziapp.id : req :",request.env.company.ngrok_url)
        
        if request.env.company.ngrok_url:
            _logger.info("\n\ndke.iziapp.id : POST : ngrok url found!")
            url = f"{request.env.company.ngrok_url}testwebhookpost"
            response = requests.post(url, json=data)
        else:
            _logger.info("\n\ndke.iziapp.id : POST : ngrok url not found!")
        super().webhookpost()
    # @http.route('/whatsapp/webhook/', methods=['POST'], type="json", auth="public")
    # def webhookpost(self):
        

    #     # Call the original method to ensure parent logic is executed
    #     super(WebController, self).webhookpost()

    
    # @http.route('/whatsapp/webhook/', methods=['GET'], type="http", auth="public", csrf=False)
    # def webhookget(self, **kwargs):
    #     _logger.info("Received GET webhook request with data: %s", kwargs)

    #     if request.env.company.ngrok_url:
    #         _logger.info("\n\n GET : ngrok url found!")
    #         url = request.env.company.ngrok_url
    #         response = requests.get(url, params=kwargs)
    #     else:
    #         _logger.info("\n\n GET : ngrok url not found!")
        
    #     super(WebController, self).webhookget(**kwargs)