# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import _, api, fields, models
from odoo.exceptions import UserError,Warning
import logging
_logger = logging.getLogger(__name__)


class Office365Synchronization(models.TransientModel):
	_name = 'office365.synchronization'
	_description = 'Transient Model For office365 Synchronization'

	@api.model
	def sync_data_from_quickbook(self,operation, getLimit, action='export'):
		bulk_synchronization = self.env['office365.bulk.synchronisation']
		instances = self.env['office365.instance'].search([])
		for instance in instances:
			limit = getattr(instance,getLimit)
			vals = {
				'action':action,
				'instance_id':instance.id,
				'object_type':operation,
				'limit':limit
			}
			sync = bulk_synchronization.create(vals)
			sync.start_action_office365_synchronization()
		return True
	
	
	def export_synchronisation(self):
		vals = {'limit':'1'}
		partial_id = self.env['office365.bulk.synchronisation'].create(vals)
		return {
			'name':'Office365 Bulk Synchronizaion',
			'view_mode': 'form',
			'view_id': False,
			'res_model': 'office365.bulk.synchronisation',
			'res_id': partial_id.id,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
			'domain': '[]',
		}
	
	def import_synchronization(self):
		vals = {'action':'import',
		'limit':'1'}
		partial_id = self.env['office365.bulk.synchronisation'].create(vals)
		return {
			'name':'Office365 Bulk Synchronizaion',
			'view_mode': 'form',
			'view_id': False,
			'res_model': 'office365.bulk.synchronisation',
			'res_id': partial_id.id,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
			'domain': '[]',
		} 
	

	def create_odoo_mapping(self, model , odoo_id, office_id, instance_id, extra_data = {}):
		'''This function is use to create Odoo mapping
		@params
			response data --> dictionary of values
			storage_type --> storage type
			model --> model to create mappings like sale.order,res.partner
		@returns 
		newly created model obj
		'''
		vals = {
			'odoo_id':odoo_id,
			'office_id':office_id,
			'name': odoo_id,
			'instance_id':instance_id
		}
		if extra_data:
			vals.update(extra_data)
		res = self.env[model].create(vals)
		return res
	

	def reset_mapping(self):
		message_wizard = self.env['office365.message.wizard']
		models = [
			'office365.account',
			'office365.partner',
		]
		message = 'SuccessFully Deleted'
		try:
			for model in models:
				ids = self.env[model].search([])
				ids.unlink()
		except Exception as e:
			message = 'Message:%s'%str(e)
		return message_wizard.generate_message(message)
		