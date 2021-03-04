from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)


class Office365ContactMapping(models.Model):
	_name = 'office365.contact.mapping'
	_inherit = 'office365.common.mapping'
	_description = 'office 365 Common mappings'

	name = fields.Many2one('res.partner', 'Odoo Contact')