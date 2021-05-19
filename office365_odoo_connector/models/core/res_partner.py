from odoo import fields, api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def write(self,vals):
        mapping = self.env['office365.contact.mapping']
        if self and 'office365' not in self._context:
            mapping.search([('name','in',self.ids)]).is_sync = 'yes'
        return super(ResPartner,self).write(vals)