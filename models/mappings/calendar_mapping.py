from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)


class Office365TaskMapping(models.Model):
	_name = 'office365.calendar.mapping'
	_inherit = 'office365.common.mapping'


	name = fields.Many2one('calendar.event', 'Odoo Calendar Id')