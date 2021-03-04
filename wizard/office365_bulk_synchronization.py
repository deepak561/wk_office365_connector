# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models
import logging
from odoo.exceptions import Warning
_logger = logging.getLogger(__name__)

connection  = 'office365.instance'


class Office365BulkSynchronization(models.TransientModel):
	_name = 'office365.bulk.synchronisation'
	_description = "Office365 Bulk Synchronization"


	@api.model
	def _get_object_type(self):
		storage_type = [
			('contact','Contact'),
			('calendar','Calendar'),
			('project','Project'),
			('task','Task'),
		]
		return storage_type
	
	@api.model
	def _get_limit(self):
		limit = [
			('1',1),
			('10',10),
			('50',50),
			('100',100),
			('200',200),
			('300',300),
			('500',500),
			('1000',1000),
			('2000',2000),
		]
		return limit

	def _default_instance_name(self):
		return self.env[connection].search([], limit=1).id

	action = fields.Selection(
		selection =[('import', 'Import Data'), ('export', 'Export Data')], 
		string = 'Action', 
		default = "export", 
		required = True,
		read_only = 1,
		help = """Import Data: Import Data From office365. Export Data:Export Data To office365""")
	
	action_2 = fields.Selection(
		selection = [('sync', 'Export'), ('update', 'Update')], 
		string = 'Action', 
		default = "sync", 
		required = True,
		read_only = 1,
		help = """Export:Export Data. Update:Update Data""")
	
	action_3 = fields.Selection(
		selection = [('import', 'Import'), ('update', 'Update')], 
		string = 'Action', 
		default = "import", 
		required = True,
		read_only = 1,
		help = """Import: Import Data. Update:Update Data""")

	instance_id = fields.Many2one(
		comodel_name = connection, 
		string = 'Instance Id', 
		default = lambda self: self._default_instance_name())
	
	object_type = fields.Selection(
		selection = '_get_object_type',
		string = "Operation"
		)
	limit = fields.Selection(
		selection = '_get_limit',
		string = 'Limit',
	)
	
	def start_action_office365_synchronization(self):
		self.ensure_one()
		if self.action=='export':
			action = self.action_2
		else:
			action = self.action_3
		method = "%s_%s_%s"%(self.action,action,self.object_type)
		office365_synchronization = self.env['office365.synchronization'].with_context(office365='office365',
		instance_id = self.instance_id.id)
		message = 'There is an issue while Synchronizing Data'
		instance_id = self.instance_id.id
		connection = self.env['office365.instance']._create_office365_connection(instance_id)
		if hasattr(office365_synchronization,method):
			return getattr(office365_synchronization,method)(connection, instance_id, int(self.limit))
		return self.env['office365.message.wizard'].generate_message(message)
