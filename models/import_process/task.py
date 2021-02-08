from odoo import _, api, fields, models
import logging
import json
import requests
import datetime
_logger = logging.getLogger(__name__)

class Office365Task(models.TransientModel):
	_inherit = 'office365.synchronization'
	
	
	def import_import_task(self,connection, instance_id, limit):
		TimeModified = connection.get('lastImportTaskDate')
		wizard_message = self.env['office365.message.wizard']
		if TimeModified:
			query = "$filter=lastModifiedDateTime ge %s&$orderby=lastModifiedDateTime"%TimeModified
		else:
			query = '$orderby=lastModifiedDateTime'
		message,TimeModified = self.import_get_task(connection, instance_id, limit, query)
		if TimeModified:
			self.env['office365.instance'].browse(instance_id).lastImporttaskDate = TimeModified
		return wizard_message.generate_message(message)
	

	def import_get_task(self, connection, instance_id, limit, statement):
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.office365']
		message = 'SuccessFully Imported All The tasks'
		TimeModified = ''
		mapping = self.env['office365.task.mapping']
		res_task = self.env['res.partner']
		try:
			headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			url+= 'tasks?%s&$top=%s'%(statement,limit)
			_logger.info("================url response==================%r",url)
			response = client.call_drive_api(url, 'GET', None , headers)
			tasks = response['value']
			for task in tasks:
				vals = self.get_import_task_vals(task, connection, instance_id)
				_logger.info("================vals==================%r",vals)
				domain = [('instance_id','=',instance_id),
				('office_id','=',task['id'])]
				TimeModified = task['lastModifiedDateTime']
				search = mapping.search(domain,limit=1)
				if search:
					search.name.write(vals)
				else:
					odoo_id = res_task.create(vals)
					self.create_odoo_mapping('office365.task.mapping', odoo_id.id, task['id'], instance_id,{'created_by':'import'
					})
		except Exception as e:
			message = 'Message:%s'%str(e)
		return message,TimeModified
	

	def get_import_task_vals(self, task, connection, instance_id):
		vals = {
			'name':task['displayName'],
			'phone': task['businessPhones'][0] if task['businessPhones'] else False,
			'mobile': task['mobilePhone'],
			'email':task['emailAddresses'][0]['address'] if task['emailAddresses'] else '',
			'comment': task['personalNotes'] or '',
		}
		address = task['homeAddress']
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
		if task.get('jobTitle'):
			title = self.env['res.partner.title'].search([('name','=',task.get('jobTitle'))],limit=1)
			if title:
				vals['title'] = title.id
			else:
				title = self.env['res.partner.title'].create({'name':task.get('jobTitle')})
				if title:
					vals['title']= title.id
		return vals

	def import_get_specific_task(self, connection, office_id, instance_id):
		mapping = self.env['office365.task.mapping']
		domain = [('office_id','=',office_id),
		('instance_id','=',instance_id)]
		task = False
		find = mapping.search(domain,limit=1)
		if find:
			task = find.odoo_id
		else:
			query = "WHERE Id='%s'"%office_id
			self.import_get_task(connection,instance_id,1,query)
			find = mapping.search(domain,limit=1)
			if find:
				task = find.odoo_id
		return task