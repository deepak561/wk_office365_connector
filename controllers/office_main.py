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

	@http.route('/wk_office365_connector/',type='http',auth='user')
	def wk_office365_connector(self, *args,**kwargs):
		cloud_connection = request.env['office365.instance']
		try:
			response = cloud_connection.search([('active','=',True)],limit =1)
			_logger.info("======================================query_string%r",kwargs)
			if response:
				get  = cloud_connection._create_office365_flow(response.id, *args, **kwargs)
			action_id = request.env.ref('wk_office365_connector.office365_connection_mapping').id
			url = "/web#id={}&action={}&model=office365.instance&view_type=form".format(response.id,action_id)
			return http.local_redirect(url)
		except Exception as e:
			_logger.error("=========Error Found While Generating Access Token==================================%r",str(e))