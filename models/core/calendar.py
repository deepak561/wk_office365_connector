from odoo import fields, api, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def write(self,vals):
        mapping = self.env['office365.calendar.mapping']
        if self and 'office365' not in self._context:
            mapping.search([('name','in',self.ids)]).is_sync = 'yes'
        return super(CalendarEvent,self).write(vals)