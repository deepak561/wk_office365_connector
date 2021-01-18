from odoo import _, api, fields, models
import logging
import json
import requests
_logger = logging.getLogger(__name__)


class Office365calendar(models.TransientModel):
	_inherit = 'office365.synchronization'

	def export_sync_calendar(self, connection, instance_id, limit, domain = []):
		mapping = self.env['office365.calendar.mapping']
		exported_ids = mapping.search([('instance_id','=',instance_id)
		]).mapped('name').ids
		domain+= [('id','not in',exported_ids)]
		to_export_ids = self.env['calendar.event'].search(domain,limit=limit)
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for calendar_id in to_export_ids:
			response = self.export_office365_calendar(connection, calendar_id, instance_id)
			_logger.info("================================response%r",response)
			if response.get('status'):
				officeId = response['officeId']
				self.create_odoo_mapping('office365.calendar.mapping', calendar_id.id, officeId, instance_id)
				successfull_ids.append(calendar_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(calendar_id.id),response['message']))
		message = 'SuccessFull calendars Exported To Office365 Are%r,UnsuccessFull calendars With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def export_update_calendar(self, connection, instance_id, limit):
		mapping = self.env['office365.calendar.mapping']
		to_update_ids = mapping.search([('instance_id','=',instance_id),
		('is_sync','=','yes')])
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for to_update in to_update_ids:
			calendar_id = to_update.name
			officeId = to_update.office_id
			response = self.update_online_calendar(connection,calendar_id, officeId, instance_id)
			if response.get('status'):
				to_update.is_sync = 'no'
				successfull_ids.append(calendar_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(calendar_id.id),response['message']))
		message = 'SuccessFull calendars Updated To Office365 Are%r,UnsuccessFull calendars With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def update_online_calendar(self,connection,calendar_id,officeId, instance_id):
		status = False
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.office365']
		message = 'SuccessFully Updated'
		if url and access_token:
			headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			url+= 'calendars/%s'%officeId
			try:
				schema = self.get_export_calendar_schema(calendar_id)
				response = client.call_drive_api(url, 'PATCH', json.dumps(schema),headers = headers)
				status = True
			except Exception as e:
				message = str(e)
		return{
			'status':status,
			'message':message
		}
			
	def get_export_calendar_schema(self, calendar_id):
		split_name =calendar_id.name.split(' ') 
		schema = {
			'emailAddresses':[{
				'address': calendar_id.email or '',
				'name': calendar_id.name or ''
			}],
			'givenName': split_name[0] if len(split_name)>1 else split_name,
			'surname': split_name[-1] if len(split_name)>1 else split_name,
			'businessPhones': [calendar_id.phone or '']

		}
		return schema
		
	def export_office365_calendar(self,connection,calendar_id, instance_id):
		status = False
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.office365']
		officeId = ''
		message = 'SuccessFully Exported'
		if url and access_token:
			headers = {
				'Content-Type': 'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			url+= 'calendars'
			try:
				schema = self.get_export_calendar_schema(calendar_id)
				_logger.info("==============================schema%r",[schema])
				response = client.call_drive_api(url, 'POST', json.dumps(schema),headers = headers)
				officeId =  response['id']
				status = True
			except Exception as e:
				message = str(e)
		return{
			'status':status,
			'officeId':officeId,
			'message':message
		}
	
	def check_online_specific_calendar(self, connection, calendar_id, instance_id):
		mapping = self.env['office365.calendar.mapping']
		domain = [('instance_id','=',instance_id),
		('name','=',calendar_id.id)]
		search = mapping.search(domain,limit=1)
		officeId = False
		if search:
			officeId = search.officeId
		else:
			response = self.export_office365_calendar(connection, calendar_id, instance_id)
			if response.get('status'):
				officeId = response['officeId']
				self.create_odoo_mapping('office365.calendar.mapping', calendar_id.id, officeId, instance_id)
		return officeId