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

class LocalController(http.Controller):
    @http.route('/testwebhookpost', methods=['POST'], type="json", auth="public")
    def testwebhookpost(self):
        data = json.loads(request.httprequest.data)
        print("\n\n data webhook :")
        print(data)

    @http.route('/testsendwhatsapp', methods=['POST'], type="json", auth="public")
    def testsendwhatsapp(self):
        data = json.loads(request.httprequest.data)
        print("\n\n data sendwhatsapp :")
        print(data)