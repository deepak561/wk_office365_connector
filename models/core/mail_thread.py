from odoo import fields, api, models
import json

import logging
_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
	_inherit = 'mail.thread'

	def _message_post_after_hook(self,new_values, msg_vals):
		self = self.sudo()
		_logger.info("=============follower_ids============%r",[new_values,msg_vals])
		try:
			office_instance = self.env['office365.instance']
			client = self.env['call.office365']
			instance_id = office_instance.search([('send_message','=',True)],limit=1)
			if instance_id and msg_vals.get('message_type','notcomment')=='comment':
				partner_ids = msg_vals.get('partner_ids',[])
				if not partner_ids:
					res_id = msg_vals.get('res_id')
					if res_id:
						partner_ids = self.env[msg_vals.get('model')].browse(res_id).message_partner_ids
						if partner_ids:
							partner_ids-= self.env.user.partner_id
				if partner_ids:
					connection =  office_instance.with_context(office365='office365',
						instance_id = instance_id.id)._create_office365_connection(instance_id.id)
					if connection.get('status'):
						url = connection.get('url')
						access_token = connection.get('access_token')
						if url and access_token:
							headers = {
								'Content-type':'application/json',
								'Accept': 'application/json',
								'Authorization':'Bearer %s'%access_token
								}
							url+= 'messages'
							vals={
								'subject':msg_vals.get('subject') or 'Odoo Email From %s'%msg_vals.get('email_from'),
								'importance':'low',
								"body":{
									"contentType":"HTML",
									"content":msg_vals.get('body','')
								},
								'toRecipients':[]
							}
							for partner in partner_ids:
								vals['toRecipients'].append({
									'emailAddress':{
										'address':partner.email or ''
									}
								})
							response = client.call_drive_api(url, 'POST', json.dumps(vals),headers = headers)
							_logger.info("============vals===%r",response)
							if response:
								message_id = response.get('id')
								url+='/%s/send/'%message_id
								headers = {
								'Content-Length':'0',
								'Authorization':'Bearer %s'%access_token
								}
								send_message = client.with_context(send_mail=True).call_drive_api(url, 'POST', None,headers = headers)
		except Exception as e:
			_logger.info("=====================Error--Mail%r",str(e))
		return super()._message_post_after_hook(new_values,msg_vals)
	

	def _notify_thread(self, message, msg_vals=False, **kwargs):
		self = self.sudo()
		office_instance = self.env['office365.instance']
		instance_id = office_instance.search([('send_message','=',True)],limit=1)
		if instance_id:
			return False
		else:
			return super()._notify_thread(message, msg_vals, **kwargs)		