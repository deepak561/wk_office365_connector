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

class Office365ManualSynchronization(models.TransientModel):
	_name = 'office365.manual.synchronisation'
	_description = "Office365 Manual Synchronization"

	@api.model
	def get_object(self, object_name):
		object_to = {
			'res.partner':'contact',
			'calendar.event':'calendar',
			'project.task':'task',
			'project.project':'project'
		}
		return object_to.get(object_name,'not_found')

	def _default_instance_name(self):
		return self.env[connection].search([], limit=1).id

	instance_id = fields.Many2one(
		comodel_name = connection, 
		string = 'Instance Id', 
		default = lambda self: self._default_instance_name())
	
	def start_action_office365_synchronization(self):
		self.ensure_one()
		object_type = self.get_object(self._context.get('active_model'))
		ids = self._context['active_ids']
		method = "%s_%s_%s"%('export','sync',object_type)
		_logger.info("==================context================%r",method)
		office365_synchronization = self.env['office365.synchronization'].with_context(office365='office365',
		instance_id = self.instance_id.id)
		message = 'There Is An Issue While Synchronizing Data'
		instance_id = self.instance_id.id
		connection = self.env['office365.instance']._create_office365_connection(instance_id)
		if hasattr(office365_synchronization,method):
			return getattr(office365_synchronization,method)(connection, instance_id,False,
			[('id','in',ids)])
		return self.env['office365.message.wizard'].generate_message(message)