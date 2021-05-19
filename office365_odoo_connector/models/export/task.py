from odoo import _, api, fields, models
import logging
import json
import requests
_logger = logging.getLogger(__name__)

from datetime import date
from datetime import datetime
from datetime import timedelta
# import re
# cleanr = re.compile('<.*?>')

get_status = {
	1:'notStarted',
	5:'inProgress',
	6:'completed',
	4:'waitingOnOthers',
	7:'deferred'
}

# def remove_html_tags(html_data):
# 	cleantext = re.sub(cleanr, '', html_data)
# 	return cleantext
	
class Office365Task(models.TransientModel):
	_inherit = 'office365.synchronization'

	def export_sync_task(self, connection, instance_id, limit=False, domain = []):
		mapping = self.env['office365.task.mapping']
		exported_ids = mapping.search([('instance_id','=',instance_id)
		]).mapped('name').ids
		domain+= [('id','not in',exported_ids)]
		if limit:
			to_export_ids = self.env['project.task'].search(domain,limit=limit)
		else:
			to_export_ids = self.env['project.task'].search(domain)
		_logger.info("================================response%r",to_export_ids)
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for task_id in to_export_ids:
			response = self.export_office365_task(connection, task_id, instance_id)
			_logger.info("================================response%r",response)
			if response.get('status'):
				office_id = response['office_id']
				self.create_odoo_mapping('office365.task.mapping', task_id.id, office_id, instance_id)
				successfull_ids.append(task_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(task_id.id),response['message']))
		message = 'SuccessFull tasks Exported To Office365 Are%r,UnsuccessFull tasks With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def export_update_task(self, connection, instance_id, limit):
		mapping = self.env['office365.task.mapping']
		to_update_ids = mapping.search([('instance_id','=',instance_id),
		('is_sync','=','yes')])
		successfull_ids, unsuccessfull_ids = [],[]
		meesage_wizard = self.env['office365.message.wizard']
		for to_update in to_update_ids:
			task_id = to_update.name
			office_id = to_update.office_id
			response = self.update_office365_task(connection,task_id, office_id, instance_id)
			if response.get('status'):
				to_update.is_sync = 'no'
				successfull_ids.append(task_id.id)
			else:
				unsuccessfull_ids.append('%s,%s'%(str(task_id.id),response['message']))
		message = 'SuccessFull tasks Updated To Office365 Are%r,UnsuccessFull tasks With Response Message Are%r'%(successfull_ids,unsuccessfull_ids)
		return meesage_wizard.generate_message(message)
	
	def update_office365_task(self,connection,task_id,office_id, instance_id):
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
			try:
				project_id = self.check_office365_specific_project(connection, task_id.project_id, instance_id)
				if project_id:
					url+= 'todo/lists/%s/tasks/%s'%(project_id,office_id)
					schema = self.get_export_task_schema(task_id)
					response = client.call_drive_api(url, 'PATCH', json.dumps(schema),headers = headers)
					status = True
			except Exception as e:
				message = str(e)
		return{
			'status':status,
			'message':message
		}
	
	def export_office365_task(self,connection,task_id, instance_id):
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
			try:
				project_id = self.check_office365_specific_project(connection,task_id.project_id, instance_id)
				if project_id:
					url+= 'todo/lists/%s/tasks'%project_id
					schema = self.get_export_task_schema(task_id)
					_logger.info("==============================schema%r",[schema,url])
					response = client.call_drive_api(url, 'POST', json.dumps(schema),headers = headers)
					office_id =  response['id']
					status = True
				else:
					message ='Error Creating project For The Task'
			except Exception as e:
				message = str(e)
		return{
			'status':status,
			'office_id':office_id,
			'message':message
		}
			
	def get_export_task_schema(self, task_id):
		_logger.info("===========context===========%r",task_id.description)
		schema = {
			'title':task_id.name,
			'body': {
				'contentType':'html',
				'content':task_id.description or task_id.name
			},
			'importance': 'high' if task_id.priority=='1' else 'low',
			'status': get_status.get(task_id.stage_id.id,'inProgress')
		}
		if task_id.date_last_stage_update:
			schema['lastModifiedDateTime'] = task_id.date_last_stage_update.isoformat()+'Z'
		if task_id.date_assign:
			schema['createdDateTime'] = task_id.date_assign.isoformat()+'Z'
		if task_id.date_deadline:
			schema['dueDateTime'] = {
					'dateTime':self.get_date(task_id.date_deadline),
					'timeZone': self._context.get('tz','UTC')
			}
		return schema
		
	
	def check_office365_specific_task(self, connection, task_id, instance_id):
		mapping = self.env['office365.task.mapping']
		domain = [('instance_id','=',instance_id),
		('name','=',task_id.id)]
		search = mapping.search(domain,limit=1)
		office_id = False
		if search:
			office_id = search.office_id
		else:
			response = self.export_office365_task(connection, task_id, instance_id)
			if response.get('status'):
				office_id = response['office_id']
				self.create_odoo_mapping('office365.task.mapping', task_id.id, office_id, instance_id)
		return office_id