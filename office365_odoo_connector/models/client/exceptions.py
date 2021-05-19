#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = "Deepak Singh Gusain <deepak.singh509@webkul.com>"

class Office365RestApiError(Exception):
	"""Generic Office365 Api error class

	To catch these, you need to import it in you code e.g. :
	from odoo.addons.office365_odoo_connector.models import execptions
	from odoo.addons.office365_odoo_connector.models.execptions import Office365RestApiError
	"""

	def __init__(self, msg, error_code=None, so_error_message='', so_error_code=None):
		self.msg = msg
		self.error_code = error_code
		self.so_error_message = so_error_message
		self.so_error_code = so_error_code

	def __str__(self):
		message=''
		if self.error_code==401:
			message='Code 401- Invalid Office365 Oauth2 Information'
		message=message+repr(self.so_error_message)
		return message

class Office365ResyncError(Office365RestApiError):
	'''
		Generic Office365ResyncError error class
		This Class Inherits Office365ResyncError Class And Will Use When Access Token Will Expire
	'''
	pass