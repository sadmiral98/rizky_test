# -*- coding: utf-8 -*-
# Copyright 2022 IZI PT Solusi Usaha Mudah
import random, json
from odoo import http, fields
from datetime import datetime, timedelta
from odoo.http import request
import requests
from bs4 import BeautifulSoup
import logging
_logger = logging.getLogger(__name__)

class WebController(http.Controller):
    @http.route('/whatsapp/webhook/', methods=['POST'], type="json", auth="public")
    def webhookpost(self):
        data = json.loads(request.httprequest.data)
        
        # Custom behavior: print the data
        _logger.info("Webhook Data: %s", json.dumps(data, indent=4))
        
        if request.env.company.ngrok_url:
            _logger.info("\n\nPOST : ngrok url found!")
            url = request.env.company.ngrok_url
            response = requests.post(url, json=data)
        else:
            _logger.info("\n\nPOST : ngrok url not found!")

        # Call the original method to ensure parent logic is executed
        super(WebController, self).webhookpost()

    
    @http.route('/whatsapp/webhook/', methods=['GET'], type="http", auth="public", csrf=False)
    def webhookget(self, **kwargs):
        _logger.info("Received GET webhook request with data: %s", kwargs)

        if request.env.company.ngrok_url:
            _logger.info("\n\n GET : ngrok url found!")
            url = request.env.company.ngrok_url
            response = requests.get(url, params=kwargs)
        else:
            _logger.info("\n\n GET : ngrok url not found!")
        
        super(WebController, self).webhookget(**kwargs)