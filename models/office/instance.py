# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################
import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError,Warning
import logging
import json
from datetime import datetime
import time
from urllib.parse import urlencode, quote_plus
_logger = logging.getLogger(__name__)

limit = [('1',1),
		('10',10),
		('50',50),
		('100',100),
		('200',200),
		('300',300),
		('500',500),
		('1000',1000),
		('2000',2000),
		]


def _unescape(text):
	##
	# Replaces all encoded characters by urlib with plain utf8 string.
	#
	# @param text source text.
	# @return The plain text.
	from urllib.parse import unquote_plus
	try:
		text = unquote_plus(text)
		return text
	except Exception as e:
		return text

class Office365Instance(models.Model):
	_name = 'office365.instance'
	_inherit = 'mail.thread'

	def get_redirect_url(self):
		config_parameter = self.env['ir.config_parameter']
		url = config_parameter.get_param('web.base.url')
		if not url.endswith('/'):
			url+= '/'
		url+= 'wk_office365_connector/'
		return url

	name = fields.Char(
		string = 'Storage Name', 
		required=True
		)
	send_message = fields.Boolean(
		string = 'Send Message',
		default = False
	)

	access_token = fields.Text(
		string = 'Access Token'
		)
		
	refresh_token = fields.Text(
		string='Refresh Token'
		)

	office365_user_id = fields.Text(
		string = 'User Id'
	)

	active = fields.Boolean(
		string = 'Active', 
		default = True
		)

	connection_status = fields.Boolean(
		string = 'Connection Status',
		default = False
		)
	
	redirect_url = fields.Char(
		string= 'Redirect Url',
		required = True,
		default = lambda self:self.get_redirect_url()
	)
	
	client_id = fields.Char(
		string = 'Client Id',
	required = True
	)

	client_key = fields.Char(
		string = 'Client Key',
		required = True
	)

	message = fields.Text(
		string = "Message",
		tracking=True
		)
		
	lastImportTaskDate = fields.Char(
		string = 'Last Import Task Date'
	)
	lastImportCalendarDate = fields.Char(
		string = 'Last Import Calendar Date'
	)
	lastImportContactDate = fields.Char(
		string = 'Last Import Contact Date'
	)

	# limit for cron 
	importContactLimit = fields.Selection(selection = limit, default='10')
	
	importCalendarLimit = fields.Selection(selection = limit, default='10')
	
	importProjectLimit = fields.Selection(selection = limit, default='10')
	
	importTaskLimit = fields.Selection(selection = limit, default='10')

	@api.model
	def create(self,vals):
		if not self._context.get('multi_instance',False) and vals.get('active',False):
			if(self.search([('active','=',True)])):
				raise Warning('Only One Active Connection Allowed')
		send_message_search = self.search([('send_message','=',True)])
		if send_message_search and len(send_message_search.ids)>1:
			raise Warning('Only One Active Connection Can Have Send Message True')
		return super().create(vals)

	def write(self,vals):
		if not self._context.get('multi_instance',False) and vals.get('active',False):
			if(self.search([('active','=',True)])):
				raise Warning('Only One Active Connection Allowed')
		send_message_search = self.search([('send_message','=',True)])
		if send_message_search and len(send_message_search.ids)>1:
			raise Warning('Only One Active Connection Can Have Send Message True')
		return super().write(vals)


	@api.model
	def _create_office365_connection(self, instance_id,refresh_token = False):
		context = self._context.copy() or {}
		context.update({'instance_id':instance_id})
		self = self.with_context(context)
		instance_obj = self.browse(instance_id)
		status = True
		error = ''
		client_id = instance_obj.client_id
		office365api = self.env['call.office365']
		access_token = instance_obj.access_token
		if refresh_token:
			url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
			headers = {
				'Content-Type': 'application/x-www-form-urlencoded'
				}
			data = {
			'client_id' : client_id,
			'redirect_uri':instance_obj.redirect_url,
			'client_secret':instance_obj.client_key,
			'refresh_token':instance_obj.refresh_token,
			'scope':'user.read mail.read',
			'grant_type':'refresh_token'
			}
			try:
				response = office365api.call_drive_api(url,'POST',data=urlencode(data, quote_via=quote_plus),headers=headers)
			except Exception as e:
				status = False
				error = str(e)
			if status:
				if 'access_token' in response:
					access_token = response['access_token']
				if 'refresh_token' in response:
					refresh_token = response['refresh_token']
				if context.get('refresh_token',True):
					instance_obj.write({'access_token':access_token,'refresh_token':refresh_token})
				self._cr.commit()
		return{
			'url':'https://graph.microsoft.com/v1.0/me/',
			'office365':office365api,
			'access_token':access_token,
			'status':status,
			'error' : error,
			'lastImportTaskDate':instance_obj.lastImportTaskDate or False,
			'lastImportCalendarDate':instance_obj.lastImportCalendarDate or False,
			'lastImportContactDate':instance_obj.lastImportContactDate or False
			}
	


	def test_connection(self):
		gen_message = self.env['office365.message.wizard']
		client_id = self.client_id
		redirect_uri = self.redirect_url
		url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
		scope = '''offline_access user.read 
Mail.ReadWrite Mail.Send Calendars.ReadWrite Contacts.ReadWrite Tasks.ReadWrite'''
		data = {
			'client_id':client_id,
			'scope':scope,
			'response_type':'code',
			'redirect_uri':redirect_uri,
			'response_mode':'query',
			'state':12345
		}
		res = requests.get(url,params=data)
		if res.status_code in [200,201]:
			  return {'name': 'Go to office365',
				  'res_model': 'ir.actions.act_url',
				  'type'     : 'ir.actions.act_url',
				  'target'   : 'self',
				  'url'      : res.url
			   }
		else:
			self.connection_status = False
			message = """Issue: Error While Getting Authorisation Code(Url Not Found)"""
		return gen_message.generate_message(message)
	

	def get_office_user_id(self):
		gen_message = self.env['office365.message.wizard']
		headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%self.access_token
			}
		url = 'https://graph.microsoft.com/v1.0/me/'
		client = self.env['call.office365']
		message = 'UserId Successfully Updated'
		try:
			response = client.call_drive_api(url, 'GET', data=None, headers = headers)
			_logger.info("======================response=========%r",[response])
			userId = response.get('id')
			self.office365_user_id = userId
		except Exception as e:
			message = str(e)
		return gen_message.generate_message(message)

	@api.model
	def _create_office365_flow(self,instance_id, *args, **kwargs):
		code = kwargs.get('code','')
		status = True
		headers = {'Content-Type':'application/x-www-form-urlencoded'}
		instance_obj = self.browse(instance_id)
		client_id = instance_obj.client_id
		clien_secret_key = instance_obj.client_key
		redirect_uri = instance_obj.redirect_url
		error = ''
		message = 'Access Token And Refresh Token Successfully Updated'
		url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
		data = {
			'client_id':client_id,
			'redirect_uri':redirect_uri,
			'client_secret':clien_secret_key,
			'scode':'user.read mail.read',
			'code':code,
			'grant_type':'authorization_code'
			}
		try:
			office365api = self.env['call.office365']
			response = office365api.call_drive_api(url,'POST',data=urlencode(data, quote_via=quote_plus),headers=headers)
		except Exception as e:
			status = False
			message = str(e)
		if status:
			if 'refresh_token' in response:
				instance_obj.refresh_token = response['refresh_token']
			if 'access_token' in response:
				instance_obj.access_token = response['access_token']
		vals={
			'message':message,
			'connection_status':status
		}
		instance_obj.write(vals)
		return{
			'status':status
		}

