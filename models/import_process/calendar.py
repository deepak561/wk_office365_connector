from odoo import _, api, fields, models
import logging
import json
import requests
from datetime import datetime
_logger = logging.getLogger(__name__)

class Office365calendar(models.TransientModel):
	_inherit = 'office365.synchronization'
	
	
	def import_import_calendar(self,connection, instance_id, limit):
		TimeModified = connection.get('lastImportCalendarDate')
		wizard_message = self.env['office365.message.wizard']
		if TimeModified:
			query = "$filter=lastModifiedDateTime gt %s&$orderby=lastModifiedDateTime"%TimeModified
		else:
			query = '$orderby=lastModifiedDateTime'
		message,TimeModified = self.import_get_calendar(connection, instance_id, limit, query)
		if TimeModified:
			self.env['office365.instance'].browse(instance_id).lastImportCalendarDate = TimeModified
		return wizard_message.generate_message(message)
	

	def import_get_calendar(self, connection, instance_id, limit, statement):
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.office365']
		message = 'SuccessFully Imported All The Calendars'
		TimeModified = ''
		mapping = self.env['office365.calendar.mapping']
		calendar_event = self.env['calendar.event']
		try:
			headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			url+= 'calendar/events?%s&$top=%s'%(statement,limit)
			response = client.call_drive_api(url, 'GET', None , headers)
			calendars = response['value']
			for calendar in calendars:
				vals = self.get_import_calendar_vals(calendar, connection, instance_id)
				_logger.info("================vals==================%r",vals)
				domain = [('instance_id','=',instance_id),
				('office_id','=',calendar['id'])]
				TimeModified = calendar['lastModifiedDateTime']
				search = mapping.search(domain,limit=1)
				if search:
					search.name.write(vals)
				else:
					odoo_id = calendar_event.create(vals)
					self.create_odoo_mapping('office365.calendar.mapping', odoo_id.id, calendar['id'], instance_id,{'created_by':'import'
					})
		except Exception as e:
			message = 'Message:%s'%str(e)
		return message,TimeModified
	

	def get_import_calendar_vals(self, calendar, connection, instance_id):
		vals = {
			'name':calendar['subject'],
			'description': calendar['body']['content'] if calendar['body'] else '',
			'location': calendar['location']['displayName'] if calendar.get('location') else '',
			'allday': calendar['isAllDay']
		}
		if calendar['isAllDay']:
			if calendar['start']:
				startDate = calendar['start']['dateTime'].split('.')[0]
				startDate = datetime.strptime(startDate,"%Y-%m-%dT%H:%M:%S")
				vals['start'] = startDate
			if calendar['end']:
				endDate = calendar['start']['dateTime'].split('.')[0]
				endDate = datetime.strptime(endDate,"%Y-%m-%dT%H:%M:%S")
				vals['stop'] = endDate
		else:
			if calendar['start']:
				startDate = calendar['start']['dateTime'].split('.')[0] 
				vals['start'] = datetime.strptime(startDate,"%Y-%m-%dT%H:%M:%S")
				endDate = calendar['end']['dateTime'].split('.')[0]
				endDateTime = datetime.strptime(endDate,"%Y-%m-%dT%H:%M:%S")
				vals['stop'] = endDateTime
		attendee_ids = []
		for attendy in calendar.get('attendees',[]):
			partner_id = self.search_partner_by_mail(attendy)
			if partner_id:
				attendee_ids.append(partner_id.id)
		vals['partner_ids']= [(6,0,attendee_ids)]
		return vals
	

	def search_partner_by_mail(self,attendy):
		res_partner = self.env['res.partner']
		email =  attendy.get('emailAddress',{}).get('address')
		name =  attendy.get('emailAddress',{}).get('name')
		partner_id = False
		if email and name:
			partner_id = res_partner.search([('email','=',email),('name','=',name)],limit=1)
			if not partner_id:
				partner_id = res_partner.create({
					'email':email,
					'name':name,
					'customer_rank':1
				})
		return partner_id