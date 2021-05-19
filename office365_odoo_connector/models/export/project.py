from odoo import _, api, fields, models
import logging
import json
import requests
_logger = logging.getLogger(__name__)

class Office365Task(models.TransientModel):
	_inherit = 'office365.synchronization'

	def export_sync_project(self, connection, instance_id, limit=False, domain = []):
		mapping = self.env['office365.project.mapping']
		exported_ids = mapping.search([('instance_id','=',instance_id)
		]).mapped('name').ids
		domain+= [('id','not in',exported_ids)]
		if limit:
			to_export_ids = self.env['project.project'].search(domain,limit=limit)
		else:
			to_export_ids = self.env['project.project'].search(domain)
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for project_id in to_export_ids:
			response = self.export_office365_project(connection, project_id, instance_id)
			_logger.info("================================response%r",response)
			if response.get('status'):
				office_id = response['office_id']
				self.create_odoo_mapping('office365.project.mapping', project_id.id, office_id, instance_id)
				successfull_ids.append(project_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(project_id.id),response['message']))
		message = 'SuccessFull Projects Exported To Office365 Are%r,UnsuccessFull Projects With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def export_update_project(self, connection, instance_id, limit):
		mapping = self.env['office365.project.mapping']
		to_update_ids = mapping.search([('instance_id','=',instance_id),
		('is_sync','=','yes')])
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for to_update in to_update_ids:
			project_id = to_update.name
			office_id = to_update.office_id
			response = self.update_office365_project(connection,project_id, office_id, instance_id)
			if response.get('status'):
				to_update.is_sync = 'no'
				successfull_ids.append(project_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(project_id.id),response['message']))
		message = 'SuccessFull Projects Updated To Office365 Are%r,UnsuccessFull Projects With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def update_office365_project(self,connection,project_id,office_id, instance_id):
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
			url+= 'todo/lists/%s'%office_id
			try:
				schema = self.get_export_project_schema(project_id)
				response = client.call_drive_api(url, 'PATCH', json.dumps(schema),headers = headers)
				status = True
			except Exception as e:
				message = str(e)
		return{
			'status':status,
			'message':message
		}
	
	def export_office365_project(self,connection,project_id, instance_id):
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
			url+= 'todo/lists'
			try:
				schema = self.get_export_project_schema(project_id)
				_logger.info("==============================schema%r",[schema,url])
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
			
	def get_export_project_schema(self, project_id):
		schema ={
			'displayName': project_id.name
		}
		return schema
		
	
	def check_office365_specific_project(self, connection, project_id, instance_id):
		mapping = self.env['office365.project.mapping']
		domain = [('instance_id','=',instance_id),
		('name','=',project_id.id)]
		search = mapping.search(domain,limit=1)
		office_id = False
		if search:
			office_id = search.office_id
		else:
			response = self.export_office365_project(connection, project_id, instance_id)
			if response.get('status'):
				office_id = response['office_id']
				self.create_odoo_mapping('office365.project.mapping', project_id.id, office_id, instance_id)
		return office_id