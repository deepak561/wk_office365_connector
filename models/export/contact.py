from odoo import _, api, fields, models
import logging
import json
import requests
_logger = logging.getLogger(__name__)


class Office365Contact(models.TransientModel):
	_inherit = 'office365.synchronization'

	def export_sync_contact(self, connection, instance_id, limit=False, domain = []):
		mapping = self.env['office365.contact.mapping']
		exported_ids = mapping.search([('instance_id','=',instance_id)
		]).mapped('name').ids
		domain+= [('id','not in',exported_ids),('parent_id','=',False),
		('email','not in', [False,'', ' '])]
		if limit:
			to_export_ids = self.env['res.partner'].search(domain,limit=limit)
		else:
			to_export_ids = self.env['res.partner'].search(domain)
		_logger.info("================================response%r",[to_export_ids,domain])
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for partner_id in to_export_ids:
			response = self.export_office365_contact(connection, partner_id, instance_id)
			if response.get('status'):
				office_id = response['office_id']
				self.create_odoo_mapping('office365.contact.mapping', partner_id.id, office_id, instance_id)
				successfull_ids.append(partner_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(partner_id.id),response['message']))
		message = 'SuccessFull Customers Exported To Office365 Are%r,UnsuccessFull Customers With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def export_update_contact(self, connection, instance_id, limit):
		mapping = self.env['office365.contact.mapping']
		to_update_ids = mapping.search([('instance_id','=',instance_id),
		('is_sync','=','yes')])
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for to_update in to_update_ids:
			partner_id = to_update.name
			office_id = to_update.office_id
			response = self.update_office365_partner(connection,partner_id, office_id, instance_id)
			if response.get('status'):
				to_update.is_sync = 'no'
				successfull_ids.append(partner_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(partner_id.id),response['message']))
		message = 'SuccessFull Customers Updated To Office365 Are%r,UnsuccessFull Customers With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def update_office365_partner(self,connection,partner_id,office_id, instance_id):
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
			url+= 'contacts/%s'%office_id
			try:
				schema = self.get_export_customer_schema(partner_id)
				response = client.call_drive_api(url, 'PATCH', json.dumps(schema),headers = headers)
				status = True
			except Exception as e:
				message = str(e)
		return{
			'status':status,
			'message':message
		}
			
	def get_export_customer_schema(self, partner_id):
		split_name =partner_id.name.split(' ') 
		schema = {
			'emailAddresses':[{
				'address': partner_id.email or '',
				'name': partner_id.name or ''
			}],
			'givenName': split_name[0] if len(split_name)>1 else split_name,
			'surname': split_name[-1] if len(split_name)>1 else split_name,
			'businessPhones': [partner_id.phone or ''],
			'jobTitle': partner_id.title or '',
			'mobilePhone': partner_id.mobile or '',
			'personalNotes': partner_id.comment or '',
			'homeAddress':{
				'city': partner_id.city or '',
				'countryOrRegion':partner_id.country_id.name if partner_id.country_id else '',
				'postalCode': partner_id.zip or '',
				'state': partner_id.state_id.name if partner_id.state_id else '',
				'street': partner_id.street or ''
			}

		}
		return schema

		
	def export_office365_contact(self,connection,partner_id, instance_id):
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
			url+= 'contacts'
			try:
				schema = self.get_export_customer_schema(partner_id)
				_logger.info("==============================schema%r",[schema])
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
	
	def check_office365_specific_partner(self, connection, partner_id, instance_id):
		mapping = self.env['office365.contact.mapping']
		domain = [('instance_id','=',instance_id),
		('name','=',partner_id.id)]
		search = mapping.search(domain,limit=1)
		office_id = False
		if search:
			office_id = search.office_id
		else:
			response = self.export_office365_contact(connection, partner_id, instance_id)
			if response.get('status'):
				office_id = response['office_id']
				self.create_odoo_mapping('office365.contact.mapping', partner_id.id, office_id, instance_id)
		return office_id