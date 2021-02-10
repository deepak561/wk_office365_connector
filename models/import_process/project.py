from odoo import _, api, fields, models
import logging
import json
import requests
import datetime
_logger = logging.getLogger(__name__)

class Office365Project(models.TransientModel):
	_inherit = 'office365.synchronization'
	
	
	def import_import_project(self,connection, instance_id, limit):
		wizard_message = self.env['office365.message.wizard']
		message = self.import_get_project(connection, instance_id, limit)
		return wizard_message.generate_message(message)
	

	def import_get_project(self, connection, instance_id, limit, query= False):
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.office365']
		message = 'SuccessFully Imported All The projects'
		TimeModified = ''
		mapping = self.env['office365.project.mapping']
		res_project = self.env['project.project']
		try:
			headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			if not query:
				url+= 'todo/lists?$top=%s'%limit
			response = client.call_drive_api(url, 'GET', None , headers)
			projects = response['value']
			for project in projects:
				vals = self.get_import_project_vals(project, connection, instance_id)
				domain = [('instance_id','=',instance_id),
				('office_id','=',project['id'])]
				search = mapping.search(domain,limit=1)
				if search:
					search.name.write(vals)
				else:
					odoo_id = res_project.create(vals)
					self.create_odoo_mapping('office365.project.mapping', odoo_id.id, project['id'], instance_id,{'created_by':'import'
					})
		except Exception as e:
			message = 'Message:%s'%str(e)
		return message
	

	def get_import_project_vals(self, project, connection, instance_id):
		vals = {
			'name':project['displayName'],
		}
		return vals