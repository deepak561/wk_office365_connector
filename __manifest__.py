# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Wk Office365 Connector",
  "summary"              :  """Bi-directional synchronization of calenders,contacts,tasks,projects with Office365""",
  "category"             :  "cloud",
  "version"              :  "1.1.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "website"              :  "http://www.webkul.com",
  "description"          :  """Wk Office365 Connector
==============================
This module establish integration between your Odoo and office365  and allows bi-directional synchronization
 of calenders, contacts, tasks and projects.


For any doubt or query email us at support@webkul.com or raise a Ticket on http://webkul.com/ticket/""",
  "depends"              :  ['crm',
  'project'],
  "data"                 :  [
    'security/office365_security.xml',
    'security/ir.model.access.csv',
    'views/office/instance.xml',
    'views/mapping/contact_mapping.xml',
    'views/mapping/calendar_mapping.xml',
    'views/mapping/task_mapping.xml',
    'views/mapping/project_mapping.xml',
    'views/office/dashboard.xml',
    'views/office/office365_synchronization.xml',
    'views/office/menu.xml',
    'wizard/office365_message.xml',
    'wizard/office365_bulk_synchronization.xml',
    'wizard/office365_manual_synchronization.xml',
    'data/cron.xml',
    'data/server.xml'],
  'qweb':[
		'static/src/xml/office365_dashboard.xml'
	],
  "images"               :  ['static/description/banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  169,
  "currency"             :  "USD",
  "external_dependencies":  {'python': ['requests']},
}
