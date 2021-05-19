from odoo import api, models
import logging
import requests
from .exceptions import Office365RestApiError,Office365ResyncError
_logger = logging.getLogger(__name__)


class CallOffice365Api(models.TransientModel):
	_name = 'call.office365'
	_description = 'Class Use To Call Office365 Api Methods'

	headers = {'User-agent': 'Office365: Python Office365 Library'}
	client = None

	@api.model
	def _parse_error(self, content):
		"""
		Take the content as string and extracts the Office365 error
		@param content: Content of the response of Office365
		@return (Office365 Error Code, Office365 Error Message)
		"""
		message = ''
		error = content.get('error')
		code = False
		if type(error)==dict:
			message = error.get('message')
			code = error.get('code')
		if 'error_description' in content:
			message = content['error_description']
		if not code:
			code = content.get('error','')
		return code,message

	@api.model
	def _check_status_code(self, response, method, url):
		"""
		Take the status code and throw an exception if the server didn't return 200 or 201 or 302 or 204 code
		@param response: response return by the client request
		@param method: request method
		@param url: request url
		@return: True or raise an exception Office365RestApiError
		"""
		message_by_code = {
			400: 'Bad Request',
			401: 'Unauthorized',
			403: 'Forbidden',
			404: 'Not Found',
			405: 'Method Not Allowed',
			406: 'Not Acceptable',
			409: 'Conflict',
			410: 'Gone',
			411: 'Length Required',
			412: 'Precondition Failed',
			413: 'Request Entity Too Large',
			415: 'Unsupported Media Type',
			416: 'Requested Range Not Satisfiable',
			422: 'Unprocessable Entity',
			429: 'Too Many Requests',
			500: 'Internal Server Error',
			501: 'Not Implemented',
			503: 'Service Unavailable',
			507: 'Insufficient Storage',
			509: 'Bandwidth Limit Exceeded',
		}
		status_code = response.status_code
		content = response.content
		_logger.info("==============================content%r",self._context)
		if status_code in (200, 201, 202, 302, 204):
			if self._context.get('send_mail',False):
				return content
			else:
				return response.json()
		else:
			content = response.json()
			so_error_code, so_error_message = self._parse_error(content)
			if so_error_code=='InvalidAuthenticationToken':
				raise Office365ResyncError(
					'Resync Required', 410, 
					'The requested resource is no longer available at the server',410)
			if status_code in message_by_code:
				raise Office365RestApiError(message_by_code[status_code],
					status_code, so_error_message, so_error_code)
		return content


	@api.model
	def call_drive_api(self,url, method, data=None, headers={}):
		"""
		Execute a request on the Office365 Rest

		@param url: full url to call
		@param method: GET, POST, PUT,PATCH,DELETE
		@param data: for PUT (edit) and POST (add) only the data sent to Office365
		@return: dictionary content and binary data content of the response
		"""
		context = self._context.copy() or {}
		if self.client==None:
			self.client = requests.Session()
		request_headers = self.headers.copy()
		request_headers.update(headers)
		r = self.client.request(method, url, data=data, headers=request_headers)
		try:
			content = self._check_status_code(r, method, url)
			return content
		except Office365ResyncError as e:
			if context.get('call_again',True):
				context['call_again'] = False
				instance_id = context.get('instance_id',False)
				if instance_id:
					connection = self.env['office365.instance']._create_office365_connection(instance_id, refresh_token =True)
					access_token = connection.get('access_token',False)
					if access_token:
						headers.update({'Authorization': 'bearer {}'.format(access_token)})
				return self.with_context(context).call_drive_api(url, method, data, headers)
			raise Office365RestApiError(
					'Required Test Connection', 410, 
					'The requested refresh token is no longer available at the server so test connection again',410)
		
		

