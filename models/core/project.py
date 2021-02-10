from odoo import fields, api, models


class ProjectProejct(models.Model):
    _inherit = 'project.project'

    def write(self,vals):
        mapping = self.env['office365.project.mapping']
        if self and 'office365' not in self._context:
            mapping.search([('name','in',self.ids)]).is_sync = 'yes'
        return super(ProjectProejct,self).write(vals)