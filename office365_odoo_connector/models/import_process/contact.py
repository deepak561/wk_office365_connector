from odoo import _, api, fields, models
import logging
import json
import requests
import datetime
_logger = logging.getLogger(__name__)

class Office365Contact(models.TransientModel):
	_inherit = 'office365.synchronization'
	
	
	def import_import_contact(self,connection, instance_id, limit):
		TimeModified = connection.get('lastImportContactDate')
		wizard_message = self.env['office365.message.wizard']
		if TimeModified:
			query = "$filter=lastModifiedDateTime gt %s&$orderby=lastModifiedDateTime"%TimeModified
		else:
			query = '$orderby=lastModifiedDateTime'
		message,TimeModified = self.import_get_contact(connection, instance_id, limit, query)
		if TimeModified:
			self.env['office365.instance'].browse(instance_id).lastImportContactDate = TimeModified
		return wizard_message.generate_message(message)
	

	def import_get_contact(self, connection, instance_id, limit, statement):
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.office365']
		message = 'SuccessFully Imported All The Contacts'
		TimeModified = ''
		mapping = self.env['office365.contact.mapping']
		res_contact = self.env['res.partner']
		try:
			headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			url+= 'contacts?%s&$top=%s'%(statement,limit)
			response = client.call_drive_api(url, 'GET', None , headers)
			contacts = response['value']
			for contact in contacts:
				vals = self.get_import_contact_vals(contact, connection, instance_id)
				domain = [('instance_id','=',instance_id),
				('office_id','=',contact['id'])]
				TimeModified = contact['lastModifiedDateTime']
				search = mapping.search(domain,limit=1)
				if search:
					search.name.write(vals)
				else:
					odoo_id = res_contact.create(vals)
					self.create_odoo_mapping('office365.contact.mapping', odoo_id.id, contact['id'], instance_id,{'created_by':'import'
					})
		except Exception as e:
			message = 'Message:%s'%str(e)
		return message,TimeModified
	

	def get_import_contact_vals(self, contact, connection, instance_id):
		vals = {
			'name':contact['displayName'],
			'phone': contact['businessPhones'][0] if contact['businessPhones'] else False,
			'mobile': contact['mobilePhone'],
			'email':contact['emailAddresses'][0]['address'] if contact['emailAddresses'] else '',
			'comment': contact['personalNotes'] or '',
		}
		address = contact['homeAddress']
		if address:
			vals.update({
				'city': address['city'],
				'zip': address['postalCode'],
				'street': address['street']
			})
			if address.get('state'):
				state = self.env['res.country.state'].search([('name','ilike',address['state'])],limit=1)
				if state:
					vals['state_id'] = state.id
			if address.get('countryOrRegion'):
				country_id = self.env['res.country'].search([('name','ilike',address['countryOrRegion'])],limit=1)
				if country_id:
					vals['country_id'] = country_id.id
		if contact.get('jobTitle'):
			title = self.env['res.partner.title'].search([('name','ilike',contact.get('jobTitle'))],limit=1)
			if title:
				vals['title'] = title.id
			else:
				title = self.env['res.partner.title'].create({'name':contact.get('jobTitle')})
				if title:
					vals['title']= title.id
		return vals