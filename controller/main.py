# -*- coding: utf-8 -*-
# Copyright 2022 IZI PT Solusi Usaha Mudah
from odoo import http, fields
from datetime import datetime, timedelta
from odoo.http import request
from bs4 import BeautifulSoup
from odoo.addons.whatsapp.controller.main import Webhook
import requests
import threading
import json
import base64

from odoo import _
from odoo.exceptions import RedirectWarning
from odoo.addons.whatsapp.tools.whatsapp_api import WhatsAppApi
from odoo.addons.whatsapp.tools.whatsapp_exception import WhatsAppError
from werkzeug.exceptions import Forbidden

import logging
_logger = logging.getLogger('dke.iziapp.id')


DEFAULT_ENDPOINT = "https://graph.facebook.com/v17.0"

# R: monkey patching
original_send_whatsapp = WhatsAppApi._send_whatsapp

def custom_api_request(self, request_type, url, auth_type="", params=False, headers=None, data=False, files=False, endpoint_include=False):
    if getattr(threading.current_thread(), 'testing', False):
        raise WhatsAppError("API requests disabled in testing.")

    headers = headers or {}
    params = params or {}
    if not all([self.token, self.phone_uid]):
        action = self.wa_account_id.env.ref('whatsapp.whatsapp_account_action')
        raise RedirectWarning(_("To use WhatsApp Configure it first"), action=action.id, button_text=_("Configure Whatsapp Business Account"))
    if auth_type == 'oauth':
        headers.update({'Authorization': f'OAuth {self.token}'})
    if auth_type == 'bearer':
        headers.update({'Authorization': f'Bearer {self.token}'})
    call_url = (DEFAULT_ENDPOINT + url) if not endpoint_include else url

    try:
        res = requests.request(request_type, call_url, params=params, headers=headers, data=data, files=files, timeout=10)
        _logger.info("res api req %s ||| %s",res,res.json())
    except requests.exceptions.RequestException:
        raise WhatsAppError(failure_type='network')

    # raise if json-parseable and 'error' in json
    try:
        if 'error' in res.json():
            raise WhatsAppError(*self.custom_prepare_error_response(res.json()))
    except ValueError:
        if not res.ok:
            raise WhatsAppError(failure_type='network')

    return res

def custom_prepare_error_response(self, response):
    """
        This method is used to prepare error response
        :return tuple[str, int]: (error_message, whatsapp_error_code | -1)
    """
    if response.get('error'):
        error = response['error']
        desc = error.get('message')
        code = error.get('code', 'odoo')
        return (desc if desc else _("{error_code} - Non-descript Error", code), code)
    return (_("Something went wrong when contacting WhatsApp, please try again later. If this happens frequently, contact support."), -1)

def get_media_id(self, file_content, file_name, mimetype):
    files = {
        'file': (file_name, file_content, mimetype),
        'type': (None, mimetype),                    # Non-file field
        'messaging_product': (None, 'whatsapp')
    }
    url = f"{DEFAULT_ENDPOINT}/{self.phone_uid}/media"
    headers={
        # 'Content-Type': 'application/json',
        'Authorization': f'Bearer {self.token}'
    }
    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        media_id = response.json().get('id')
        return media_id
    return media_id

def custom_process_image(self, data, send_vals):
    attachment = request.env['ir.attachment'].sudo().browse(1341)
    file_content = base64.b64decode(attachment.datas)
    file_name = attachment.name
    mimetype = attachment.mimetype
    media_id = self.get_media_id(file_content, file_name, mimetype)
    data.update({
        'type': 'image',
        'image': {
            'id' : media_id,
            'caption': send_vals.get('body'),
        }
    })
    return data

def custom_process_document(self, data, send_vals):
    attachment = request.env['ir.attachment'].sudo().browse(1340)
    file_content = base64.b64decode(attachment.datas)
    file_name = attachment.name
    mimetype = attachment.mimetype
    media_id = self.get_media_id(file_content, file_name, mimetype)
    data.update({
        'type': 'document',
        'document': {
            'id' : media_id,
            'caption': send_vals.get('body'),
            'filename': 'doc_filename.pdf'
        }
    })
    return data

def custom_process_list(self, data, send_vals, records_to_button):
    section_rows = []
    for records in records_to_button:
        section_rows.append({
            'id': 'row_'+str(records.get('id')),
            'title': records.get('category'), # R: Max Char is 24 Chars
            'description': records.get('name')
        })
    data.update({
        'type': 'interactive',
        'interactive': {
            'type': 'list',
            'header': {
                'type':'text',
                'text': 'Testing Reply Button'
            },
            'body': {
                'text': send_vals.get('body')
            },
            'footer': {
                'text': 'Select 1 item'
            },
            'action': {
                'sections': [
                    {
                        'title': 'SECTION Title',
                        'rows': section_rows
                        # 'rows': [{'id':}]
                    }
                ],
                'button': 'Open Option',
            }
        }
    })
    return data

def custom_process_button(self, data, send_vals):
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
    return data
def custom_send_whatsapp(self, number, message_type, send_vals, parent_message_id=False, records_to_button=[]):
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
        # BUtton reply chat
        # data = self.custom_process_button(data, send_vals)

        if records_to_button:
            _logger.info("yes records ")
            # List reply chat
            data = self.custom_process_list(data, send_vals, records_to_button)
        _logger.info("DATA : %s", data)
        # document reply chat
        # data = self.custom_process_document(data, send_vals)

        # Image reply chat
        # data = self.custom_process_image(data, send_vals)

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
    _logger.info("response ::>> %s",response_json)
    if response_json.get('messages'):
        msg_uid = response_json['messages'][0]['id']
        return msg_uid
    raise WhatsAppError(*self.custom_prepare_error_response(response_json))

WhatsAppApi.custom_api_request = custom_api_request
WhatsAppApi.custom_prepare_error_response = custom_prepare_error_response
WhatsAppApi.get_media_id = get_media_id
WhatsAppApi.custom_process_image = custom_process_image
WhatsAppApi.custom_process_document = custom_process_document
WhatsAppApi.custom_process_list = custom_process_list
WhatsAppApi.custom_process_button = custom_process_button
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
            _logger.info("\n\ndke.iziapp.id : POST : ngrok url NOT found!")

        for entry in data['entry']:
            account_id = entry['id']
            account = request.env['whatsapp.account'].sudo().search(
                [('account_uid', '=', account_id)])
            if not self._check_signature(account):
                raise Forbidden()

            for changes in entry.get('changes', []):
                value = changes['value']
                phone_number_id = value.get('metadata', {}).get('phone_number_id', {})
                if not phone_number_id:
                    phone_number_id = value.get('whatsapp_business_api_data', {}).get('phone_number_id', {})
                if phone_number_id:
                    _logger.info("\n\ndke.iziapp.id PHONE NUMBER %s", phone_number_id)
                    wa_account_id = request.env['whatsapp.account'].sudo().search([
                        ('phone_uid', '=', phone_number_id), ('account_uid', '=', account_id)])
                    _logger.info("\n\ndke.iziapp.id wa_account_id %s", wa_account_id)
                    if wa_account_id:
                        # Process Messages and Status webhooks
                        if changes['field'] == 'messages':
                            _logger.info("\n\ndke.iziapp.id yes change val")
                            _logger.info("\n\ndke.iziapp.id value %s", value)
                            request.env['whatsapp.message']._process_statuses(value)
                            wa_account_id._process_messages(value)
                    else:
                        _logger.warning("There is no phone configured for this whatsapp webhook : %s ", data)

                # Process Template webhooks
                if value.get('message_template_id'):
                    # There is no user in webhook, so we need to SUPERUSER_ID to write on template object
                    template = request.env['whatsapp.template'].sudo().search([('wa_template_uid', '=', value['message_template_id'])])
                    if template:
                        if changes['field'] == 'message_template_status_update':
                            template.write({'status': value['event'].lower()})
                            description = value.get('other_info', {}).get('description', {}) or value.get('reason', {})
                            if description:
                                template.message_post(
                                    body=_("Your Template has been rejected.") + Markup("<br/>") + _("Reason : %s", description))
                            continue
                        if changes['field'] == 'message_template_quality_update':
                            template.write({'quality': value['new_quality_score'].lower()})
                            continue
                        if changes['field'] == 'template_category_update':
                            template.write({'template_type': value['new_category'].lower()})
                            continue
                        _logger.warning("Unknown Template webhook : %s ", value)
                    else:
                        _logger.warning("No Template found for this webhook : %s ", value)
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