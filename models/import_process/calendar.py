from odoo import _, api, fields, models
import logging
import json
import requests
import datetime
_logger = logging.getLogger(__name__)

class Office365calendar(models.TransientModel):
	_inherit = 'office365.synchronization'
	
	
	def import_import_calendar(self,connection, instance_id, limit):
		TimeModified = connection.get('lastImportCalendarDate')
		wizard_message = self.env['office365.message.wizard']
		if TimeModified:
			query = "$filter=lastModifiedDateTime ge %s&$orderby=lastModifiedDateTime"%TimeModified
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
			_logger.info("================url response==================%r",url)
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
			'name':calendar['displayName'],
			'phone': calendar['businessPhones'][0] if calendar['businessPhones'] else False,
			'mobile': calendar['mobilePhone'],
			'email':calendar['emailAddresses'][0]['address'] if calendar['emailAddresses'] else '',
			'comment': calendar['personalNotes'] or '',
		}
		address = calendar['homeAddress']
		if address:
			vals.update({
				'city': address['city'],
				'zip': address['postalCode'],
				'street': address['street']
			})
			if address.get('state'):
				state = self.env['res.country.state'].search([('name','=',address['state'])],limit=1)
				if state:
					vals['state_id'] = state.id
			if address.get('countryOrRegion'):
				country_id = self.env['res.country'].search([('name','=',address['countryOrRegion'])],limit=1)
				if country_id:
					vals['country_id'] = country_id.id
		if calendar.get('jobTitle'):
			title = self.env['res.partner.title'].search([('name','=',calendar.get('jobTitle'))],limit=1)
			if title:
				vals['title'] = title.id
			else:
				title = self.env['res.partner.title'].create({'name':calendar.get('jobTitle')})
				if title:
					vals['title']= title.id
		return vals