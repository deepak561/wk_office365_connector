from odoo import fields, api, models
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def write(self,vals):
        # _logger.info("============vals%r==============",[vals,self._context])
        # vals['start'] = datetime.now()
        # vals['stop'] = datetime.now()
        mapping = self.env['office365.calendar.mapping']
        if self and 'office365' not in self._context:
            mapping.search([('name','in',self.ids)]).is_sync = 'yes'
        return super(CalendarEvent,self).write(vals)