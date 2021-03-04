from odoo import _, api, fields, models
import logging
import json
import requests
from datetime import datetime
from dateutil import parser
import math
_logger = logging.getLogger(__name__)

get_status = {
	'notStarted':1,
	'inProgress':5,
	'completed':6,
	'waitingOnOthers':4,
	'deferred':7
}

class Office365Task(models.TransientModel):
	_inherit = 'office365.synchronization'
	
	
	def import_import_task(self,connection, instance_id, limit):
		TimeModified = connection.get('lastImportTaskDate')
		wizard_message = self.env['office365.message.wizard']
		if TimeModified:
			query = "$filter=lastModifiedDateTime gt %s&$orderby=lastModifiedDateTime"%TimeModified
		else:
			query = '$orderby=lastModifiedDateTime'
		message = self.import_get_task(connection, instance_id, limit, query)
		return wizard_message.generate_message(message)
	

	def import_get_task(self, connection, instance_id, limit, statement):
		url = connection.get('url')
		access_token = connection.get('access_token')
		client = self.env['call.office365']
		message = 'SuccessFully Imported All The tasks'
		TimeModified = ''
		mapping = self.env['office365.task.mapping']
		project_task = self.env['project.task']
		projects = self.env['office365.project.mapping'].search([('instance_id','=',instance_id)])
		if not projects:
			return 'Please Import Project First'
		try:
			headers = {
				'Content-type':'application/json',
				'Accept': 'application/json',
				'Authorization':'Bearer %s'%access_token
			}
			for project in projects:
				get_url = url + 'todo/lists/%s/tasks?%s&$top=%s'%(project.office_id,statement,limit)
				_logger.info("=============get_url====================%r",get_url)
				response = client.call_drive_api(get_url, 'GET', None , headers)
				tasks = response['value']
				for task in tasks:
					vals = self.get_import_task_vals(task, connection, instance_id)
					vals['project_id'] = project.name.id
					domain = [('instance_id','=',instance_id),
					('office_id','=',task['id'])]
					TimeModified = task['lastModifiedDateTime']
					search = mapping.search(domain,limit=1)
					if search:
						search.name.write(vals)
					else:
						odoo_id = project_task.create(vals)
						self.create_odoo_mapping('office365.task.mapping', odoo_id.id, task['id'], instance_id,{'created_by':'import'
						})
				if TimeModified:
					self.env['office365.instance'].browse(instance_id).lastImportTaskDate = TimeModified
		except Exception as e:
			message = 'Message:%s'%str(e)
		return message
	

	def get_import_task_vals(self, task, connection, instance_id):
		vals = {
			'name':task['title'],
			'description': task['body']['content'] if task['body'] else '',
			'priority': '1' if task['importance']=='high' else '0',
			'stage_id': get_status.get(task['status'],1),
		}
		if task.get('lastModifiedDateTime'):
			lastModifiedDateTime = task['lastModifiedDateTime'].split('.')[0] 
			vals['date_last_stage_update'] = datetime.strptime(lastModifiedDateTime,"%Y-%m-%dT%H:%M:%S")
		if task.get('createdDateTime'):
			createdDateTime = task['createdDateTime'].split('.')[0]
			vals['date_assign'] = datetime.strptime(createdDateTime,"%Y-%m-%dT%H:%M:%S")
		if task.get('dueDateTime'):
			dueDateTime = task['dueDateTime']['dateTime'].split('.')[0]
			dueDateTime = datetime.strptime(dueDateTime,"%Y-%m-%dT%H:%M:%S")
			vals['date_deadline'] = dueDateTime.date()
		return vals