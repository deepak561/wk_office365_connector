# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models


class Office365MessageWizard(models.TransientModel):
	_name = "office365.message.wizard"
	_description = "Message Wizard For Quickbook Online View"
	
	text = fields.Text(string='Message', readonly=True, translate=True)

	def generate_message(self, message, name='Message/Summary'):
		partial_id = self.create({'text':message}).id
		return {
			'name':name,
			'view_mode': 'form',
			'view_id': False,
			'res_model': 'office365.message.wizard',
			'res_id': partial_id,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
			'domain': '[]',
		}
