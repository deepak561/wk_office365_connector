from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)


class Office365TaskMapping(models.Model):
	_name = 'office365.task.mapping'
	_inherit = 'office365.common.mapping'
	_description = 'office 365 Common mappings'

	name = fields.Many2one('project.task', 'Odoo Task')