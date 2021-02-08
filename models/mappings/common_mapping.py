from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)


class Office365CommonMapping(models.Model):
	_name = 'office365.common.mapping'
	_description = 'office 365 Common mappings'


	odoo_id = fields.Integer('Odoo Id')
	office_id = fields.Char('Office365 Contact Id')
	instance_id = fields.Many2one('office365.instance')
	created_by = fields.Char('Created By', default = 'export')
	is_sync = fields.Selection([('yes','Yes'),('no','No')],'Update Required', default='no')
