from odoo import fields, api, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def write(self,vals):
        mapping = self.env['office365.task.mapping']
        if self and 'office365' not in self._context:
            mapping.search([('name','in',self.ids)]).is_sync = 'yes'
        return super(ProjectTask,self).write(vals)