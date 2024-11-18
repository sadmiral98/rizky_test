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
from odoo import _
from odoo.addons.whatsapp.tools.whatsapp_api import WhatsAppApi
from odoo.addons.whatsapp.tools.whatsapp_exception import WhatsAppError

# R: monkey patching
original_send_whatsapp = WhatsAppApi._send_whatsapp
print("\n\n whangsaff")
print(original_send_whatsapp)
# print(WhatsAppApi.__api_requests)

def custom_api_request(self, request_type, url, auth_type="", params=False, headers=None, data=False, files=False, endpoint_include=False):
    # Call the original __api_requests function from WhatsAppApi
    return super(WhatsAppApi, self).__api_requests(
        request_type,
        url,
        auth_type=auth_type,
        params=params,
        headers=headers,
        data=data,
        files=files,
        endpoint_include=endpoint_include
    )

WhatsAppApi.custom_api_request = custom_api_request
def custom_send_whatsapp(self, number, message_type, send_vals, parent_message_id=False):
    """ Send WA messages for all message type using WhatsApp Business Account

    API Documentation:
        Normal        - https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages
        Template send - https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates
    """
    data = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': number
    }
    # if there is parent_message_id then we send message as reply
    if parent_message_id:
        data.update({
            'context': {
                'message_id': parent_message_id
            },
        })
    if message_type in ('template','document', 'image', 'audio', 'video'):
        data.update({
            'type': message_type,
            message_type: send_vals
        })
    if message_type == 'text':
        data.update({
            'type': 'interactive',
            'interactive': {
                'type': 'button',
                'header': {
                    'type':'text',
                    'text': 'Testing Reply Button'
                },
                'body': {
                    'text': send_vals.get('body')
                },
                'action': {
                    'buttons': [
                        {
                        'type': 'reply',
                        'reply': {
                            'id': 'reply-yes',
                            'title': 'Yeah !'
                            }
                        },
                        {
                        'type': 'reply',
                        'reply': {
                            'id': 'reply-no',
                            'title': 'Nope ?!'
                            }
                        }
                    ]
                }
            }
        })

    json_data = json.dumps(data)
    _logger.info("Send %s message from account %s [%s]", message_type, self.wa_account_id.name, self.wa_account_id.id)
    response = self.custom_api_request(
        "POST",
        f"/{self.phone_uid}/messages",
        auth_type="bearer",
        headers={'Content-Type': 'application/json'},
        data=json_data
    )
    response_json = response.json()
    if response_json.get('messages'):
        msg_uid = response_json['messages'][0]['id']
        return msg_uid
    raise WhatsAppError(*self._prepare_error_response(response_json))

WhatsAppApi._send_whatsapp = custom_send_whatsapp
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