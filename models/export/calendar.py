from odoo import _, api, fields, models
import json
import requests
from datetime import date
from datetime import datetime
from datetime import timedelta
import logging
# import re

# cleanr = re.compile('<.*?>')
_logger = logging.getLogger(__name__)

get_rule = {
	'daily':'daily',
	'weekly':'weekly',
	'monthly':'absoluteMonthly',
	'yearly':'absoluteYearly'
}

# def remove_html_tags(html_data):
# 	cleantext = re.sub(cleanr, '', html_data)
# 	return cleantext


class Office365Calendar(models.TransientModel):
	_inherit = 'office365.synchronization'

	def export_sync_calendar(self, connection, instance_id, limit = False, domain = []):
		mapping = self.env['office365.calendar.mapping']
		exported_ids = mapping.search([('instance_id','=',instance_id)
		]).mapped('name').ids
		domain+= [('id','not in',exported_ids)]
		if limit:
			to_export_ids = self.env['calendar.event'].search(domain,limit=limit)
		else:
			to_export_ids = self.env['calendar.event'].search(domain)
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for calendar_id in to_export_ids:
			response = self.export_office365_calendar(connection, calendar_id, instance_id)
			if response.get('status'):
				office_id = response['office_id']
				self.create_odoo_mapping('office365.calendar.mapping', calendar_id.id, office_id, instance_id)
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
			office_id = to_update.office_id
			response = self.update_office365_calendar(connection,calendar_id, office_id, instance_id)
			if response.get('status'):
				to_update.is_sync = 'no'
				successfull_ids.append(calendar_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(calendar_id.id),response['message']))
		message = 'SuccessFull calendars Updated To Office365 Are%r,UnsuccessFull calendars With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def update_office365_calendar(self,connection,calendar_id,office_id, instance_id):
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
			url+= 'calendar/events/%s'%office_id
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
	
	def get_date(self,date):
		date_update = datetime.combine(date, datetime.min.time())
		return date_update.isoformat()
			
	def get_export_calendar_schema(self, calendar_id):
		schema = {
			'subject':calendar_id.name,
			'body': {
				'contentType':'HTML',
				'content': calendar_id.description or calendar_id.name
			},
			"location":{
      			"displayName":calendar_id.location or ''
  				},
			"attendees": [
  		],
		}
		for partner_id in calendar_id.partner_ids:
			schema['attendees'].append({
      				"emailAddress": {
        					"address":partner_id.email or '',
        					"name": partner_id.name
      				},
      				"type": "required"
    			})
		if calendar_id.allday:
			schema['isAllDay'] = True
			if calendar_id.start_date:
				schema['start'] = {
					'dateTime':self.get_date(calendar_id.start_date),
					'timeZone': self._context.get('tz','UTC')
				}
				if (calendar_id.stop_date- calendar_id.start_date).days>0:
					endDatetime = self.get_date(calendar_id.stop_date)
				else:
					endDatetime = self.get_date(calendar_id.stop_date+timedelta(days=1))
				schema['end'] = {
					'dateTime': endDatetime,
					'timeZone':self._context.get('tz','UTC')
				}
		else:
			if calendar_id.start_datetime:
				schema['start'] = {
					'dateTime': calendar_id.start_datetime.isoformat(),
					'timeZone': self._context.get('tz','UTC')
				}
				if calendar_id.duration:
					endDatetime = calendar_id.start_datetime + timedelta(hours=calendar_id.duration)
					schema['end'] = {
						'dateTime': endDatetime.isoformat(),
						'timeZone':self._context.get('tz','UTC')
					}
		if calendar_id.alarm_ids:
			schema['isReminderOn'] = True
		return schema
		
	def export_office365_calendar(self,connection,calendar_id, instance_id):
		status = False
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.office365']
		office_id = ''
		message = 'SuccessFully Exported'
		if url and access_token:
			headers = {
				'Content-Type': 'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			url+= 'calendar/events'
			try:
				schema = self.get_export_calendar_schema(calendar_id)
				response = client.call_drive_api(url, 'POST', json.dumps(schema),headers = headers)
				office_id =  response['id']
				status = True
			except Exception as e:
				message = str(e)
		return{
			'status':status,
			'office_id':office_id,
			'message':message
		}
	
	def check_office365_specific_calendar(self, connection, calendar_id, instance_id):
		mapping = self.env['office365.calendar.mapping']
		domain = [('instance_id','=',instance_id),
		('name','=',calendar_id.id)]
		search = mapping.search(domain,limit=1)
		office_id = False
		if search:
			office_id = search.office_id
		else:
			response = self.export_office365_calendar(connection, calendar_id, instance_id)
			if response.get('status'):
				office_id = response['office_id']
				self.create_odoo_mapping('office365.calendar.mapping', calendar_id.id, office_id, instance_id)
		return office_id