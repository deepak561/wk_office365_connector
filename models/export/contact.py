from odoo import _, api, fields, models
import logging
import json
import requests
_logger = logging.getLogger(__name__)


class Office365partner(models.TransientModel):
	_inherit = 'office365.synchronization'

	def export_sync_contact(self, connection, instance_id, limit, domain = []):
		mapping = self.env['office365.contact.mapping']
		exported_ids = mapping.search([('instance_id','=',instance_id)
		]).mapped('name').ids
		domain+= [('id','not in',exported_ids),('customer_rank','=',1),
		('email','not in', [False,'', ' '])]
		to_export_ids = self.env['res.partner'].search( domain,limit=limit)
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for partner_id in to_export_ids:
			response = self.export_online_partner(connection, partner_id, instance_id)
			if response.get('status'):
				quickbook_id = response['quickbook_id']
				self.create_odoo_mapping('office365.contact.mapping', partner_id.id, quickbook_id, instance_id)
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
			quickbook_id = to_update.quickbook_id
			response = self.update_online_partner(connection,partner_id,quickbook_id, instance_id)
			if response.get('status'):
				to_update.is_sync = 'no'
				successfull_ids.append(partner_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(partner_id.id),response['message']))
		message = 'SuccessFull Customers Updated To Quickbook Are%r,UnsuccessFull Customers With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def update_online_partner(self,connection,partner_id,quickbook_id, instance_id):
		status = False
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.quickbook.api']
		message = 'SuccessFully Updated'
		if url and access_token:
			headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			get_url = url + 'customer/%s'%quickbook_id
			try:
				get_partner_object = client.call_online_api(get_url,'GET',None, headers=headers)
			except:
				pass
			url+= 'customer'
			schema = self.get_export_customer_schema(partner_id)
			schema['Id'] = str(quickbook_id)
			schema['SyncToken'] = '0'
			try:
				response = client.call_online_api(url, 'POST', json.dumps(schema),headers = headers)
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
			'PrimaryEmailAddr':{
				'Address': partner_id.email or ''
			},
			'DisplayName':partner_id.name,
			'Suffix':partner_id.title.name or '',
			'Title': partner_id.title.name or '',
			'FamilyName': split_name[0],
			'MiddleName': split_name[1] if len(split_name)>1 else split_name[0],
			'GivenName': split_name[-1],
			'Notes': partner_id.comment or '',
			'PrimaryPhone': {
				'FreeFormNumber': partner_id.phone or ''
			},
			'BillAddr': {
				'CountrySubDivisionCode': partner_id.state_id.code or '',
				'City': partner_id.city or '',
				'PostalCode': partner_id.zip or '',
				'Line1': partner_id.street or '',
				'Line2': partner_id.street2 or '',
				'Country': partner_id.country_id.code or ''
			},
			'ShipAddr': {
				'CountrySubDivisionCode': partner_id.state_id.code or '',
				'City': partner_id.city or '',
				'PostalCode': partner_id.zip or '',
				'Line1': partner_id.street or '',
				'Line2': partner_id.street2 or '',
				'Country': partner_id.country_id.code or ''
			},
			'ResaleNum': partner_id.vat or '',
			'Mobile':{
				'FreeFormNumber': partner_id.mobile or ''
			},
			'WebAddr':{
				'URI':partner_id.website or ''
			}
		}
		return schema

		
	def export_online_partner(self,connection,partner_id, instance_id):
		status = False
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.quickbook.api']
		quickbook_id = ''
		message = 'SuccessFully Exported'
		if url and access_token:
			headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			url+= 'customer'
			parent_id = False
			if partner_id.parent_id:
				parent_id = self.check_online_specific_partner(connection, partner_id.parent_id, instance_id)
			schema = self.get_export_customer_schema(partner_id)
			if parent_id:
				schema.update({
					'Job':True,
					'ParentRef':{
						'value': parent_id
						}})
			try:
				response = client.call_online_api(url, 'POST', json.dumps(schema),headers = headers)
				quickbook_id =  response.get('Customer')['Id']
				status = True
			except Exception as e:
				message = str(e)
		return{
			'status':status,
			'quickbook_id':quickbook_id,
			'message':message
		}
	

	def check_online_specific_partner(self, connection, partner_id, instance_id):
		mapping = self.env['office365.contact.mapping']
		domain = [('instance_id','=',instance_id),
		('name','=',partner_id.id)]
		search = mapping.search(domain,limit=1)
		quickbook_id = False
		if search:
			quickbook_id = search.quickbook_id
		else:
			response = self.export_online_partner(connection, partner_id, instance_id)
			if response.get('status'):
				quickbook_id = response['quickbook_id']
				self.create_odoo_mapping('office365.contact.mapping', partner_id.id, quickbook_id, instance_id)
		return quickbook_id