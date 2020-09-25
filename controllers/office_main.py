# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   "License URL : <https://store.webkul.com/license.html/>"
#
##########################################################################

import logging
from odoo import http
from odoo.http import request
_logger = logging.getLogger(__name__)


class Office365Main(http.Controller):

	@http.route('/wk_office365_connector/<string:query_string>',type='http',auth='user')
	def wk_office365_connector(self, query_string, *args,**kwargs):
		cloud_connection = request.env['office365.instance']
		try:
			response = cloud_connection.search([('query_string','=',query_string)],limit =1)
			if response:
				get  = cloud_connection._create_office365_flow(response.id, *args, **kwargs)
			action_id = request.env.ref('wk_office365_connector.office365_connection_mapping').id
			url = "/web#id={}&action={}&model=office365.instance&view_type=form".format(response.id,action_id)
			return http.local_redirect(url)
		except Exception as e:
			_logger.error("=========Error Found While Generating Access Token==================================%r",str(e))