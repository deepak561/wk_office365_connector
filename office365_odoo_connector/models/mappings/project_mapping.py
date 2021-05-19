from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)


class Office365ProjectMapping(models.Model):
	_name = 'office365.project.mapping'
	_inherit = 'office365.common.mapping'
	_description = 'office 365 Project mappings'

	name = fields.Many2one('project.project', 'Odoo Project')