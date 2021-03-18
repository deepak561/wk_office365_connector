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
from datetime import datetime
_logger = logging.getLogger(__name__)

# month = {"January": 'Jan', "February": 'Feb', "March":'Mar',"April":'Apr',"May":'May',"June":'Jun',"July":'Jul',"August":'Aug',"September":'Sep',"October":'Oct',
# 	"November":'Nov',"December":'Dec'}

month_name = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

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
	

	@http.route('/wk_office365_connector/fetch_instace_id',type='json',auth='user')
	def fetch_instace_id(self,*args, **kwargs):
		instance_id = request.session.get('instance_id',False)
		instance_env = request.env['office365.instance']
		if not instance_id:
			connection = instance_env.search([('active','=',True)],limit=1)
			request.session['instance_id'] = connection.id
			instance_id = connection.id
		current_date = datetime.now().strftime("%d %b %Y")
		task_states = request.env['office365.instance'].browse(instance_id).task_states
		_logger.info("======================================task_states%r",task_states.ids)
		return {'instance_id':instance_id,'current_date':current_date,'task_states':task_states.ids}
	
	@http.route('/wk_office365_connector/change_instance_id',type='json',auth='user')
	def change_instance_id(self,instance_id=1):
		request.session['instance_id'] = int(instance_id)
		return {'instance_id':int(instance_id)}
	

	@http.route('/wk_office365_connector/fetch_instace_details',type='json',auth='user')
	def fetch_instace_details(self,*args, **kwargs):
		selection_instance = {}
		connection = request.env['office365.instance'].search([('active','=',True)])
		for instance in connection:
			selection_instance[instance.id] = instance.name
		return selection_instance
	

	@http.route('/wk_office365_connector/fetch_instance_extra_details',type='json',auth='user')
	def fetch_instance_extra_details(self,instance_id = False,*args, **kwargs):
		data = {}
		models = {'contact':'office365.contact.mapping','task':'office365.task.mapping',
		'calendar':'office365.calendar.mapping',
		'project':'office365.project.mapping'}
		odoo_contact = request.env['office365.contact.mapping'].search_count([('created_by','=','export')])
		for key,value in models.items():
			html = ''
			count = request.env[value].search_count([('instance_id','=',instance_id)])
			data[key] = {
				'count':count,
			}
			html = self.get_graph_html(instance_id, count, value,html,'#EB3C00','import')
			html = self.get_graph_html(instance_id, count, value,html,'#A4609D')
			data[key]['html'] = html
		return {'data':data, 'odoo_contact':odoo_contact}
	
	def get_graph_html(self,instance_id, count, model,html,color, operation='export'):
		if not count:
			percentage = 0
		else:
			count_operation = request.env[model].search_count([('created_by','=',operation)])
			percentage = int((count_operation*100)/count)
		html+= '''
			<span style="background-color: {};flex: 0 0 {}%;height:5px;"></span>
		'''.format(color,percentage)
		return html
	
	@http.route('/wk_office365_connector/get_synchronisation_id', type ='json', auth='user')
	def get_synchronisation_id(self, action='export', instance=1, *args, **kwargs):
		bulk_synchronization = request.env['office365.bulk.synchronisation']
		vals = {
				'action':action,
				'instance_id':int(instance)
			}
		sync = bulk_synchronization.create(vals)
		return {'id':sync.id}

	@http.route('/wk_office365_connector/fetch_calendar_events_details',type='json',auth='user')
	def fetch_calendar_events_details(self, instance_id=1,created_by='export'):
		current_date = datetime.now().strftime("%d %b %Y")
		select_sql_clause = """select name,start from calendar_event where id in 
		(select name from office365_calendar_mapping where instance_id=%d and created_by=%r) and start >= current_date order by start asc limit %d"""%(int(instance_id),str(created_by),5)
		request.env.cr.execute(select_sql_clause)
		query_results = request.env.cr.dictfetchall()
		_logger.info("======================================query_results%r",query_results)
		res = []
		for result in query_results:
			dt = result['start']
			t = dt.strftime('%d-%b-%y:%H-%M')
			_logger.info("======================================t%r",t)
			date,time = t.split(":")
			_logger.info("=========================date:%r=============time:%r",date,time)
			data = {'name':result['name'],'date':date.replace('-',' '),'time':time.replace('-',':')}
			res.append(data)
		return res


	@http.route('/wk_office365_connector/calender_month_detail',type='json',auth='user')
	def calender_month_detail(self, instance_id=1,created_by='export',month=False):
		current_date = datetime.now().strftime("%d %m %Y")
		# month = current_date.split(' ')[1]
		_logger.info("==================calender_month_detail====================month%r",month)
		res = {'date':[],'month':0}
		if month:
			month = month_name[month]
			select_sql_clause = """select name,start from calendar_event where id in 
			(select name from office365_calendar_mapping where instance_id=%d and created_by=%r) and to_char(start,'Mon') ='%s'"""%(int(instance_id),str(created_by),str(month))
		else:
			month = current_date.split(' ')[1]
			month = month_name[int(month)]
			select_sql_clause = """select name,start from calendar_event where id in 
			(select name from office365_calendar_mapping where instance_id=%d and created_by=%r) and to_char(start,'Mon') ='%s'"""%(int(instance_id),str(created_by),str(month))
		request.env.cr.execute(select_sql_clause)
		query_results = request.env.cr.dictfetchall()
		_logger.info("==================calender_month_detail====================query_results%r",query_results)
		# res = []
		for result in query_results:
			dt = result['start']
			t = dt.strftime('%d-%m-%y:%H-%M')
			date,time = t.split(":")
			m = date.split('-')[1]
			d = date.split('-')[0]
			_logger.info("=========================date:%r=============time:%r",date,time)
			# data = {'name':result['name'],'date':date.replace('-',' '),'time':time.replace('-',':')}
			res['date'].append(int(d))
			res['month'] = int(m)-1
		_logger.info("=========================calender_month_detail=============res:%r",res)
		return res


	@http.route('/wk_office365_connector/fetch_project_details',type='json',auth='user')
	def fetch_project_details(self, instance_id=1):
		project = request.env['project.project'].search([])
		res = []

		select_sql_clause = """select count(pt.name), project_id, otm.odoo_id from office365_project_mapping otm left outer join
		project_task pt on (otm.name = pt.project_id) where otm.instance_id=%d group by project_id, odoo_id order by pt.project_id asc limit %d"""%(int(instance_id),5)

		# select_sql_clause = """select count(t.name) ,project_id from project_task t inner join 
		# office365_project_mapping m on (t.project_id = m.name) where m.instance_id=%d group by project_id"""%int(instance_id)
		request.env.cr.execute(select_sql_clause)
		query_results = request.env.cr.dictfetchall()

		_logger.info("======================================query_results%r",query_results)


		for check in query_results:
			name = request.env['project.project'].browse(int(check['odoo_id'])).name
			rec = {
				'name': name,
				'vals': check['count']
			}
			res.append(rec)
		_logger.info("======================================res%r",res)
		return res
	
	@http.route('/wk_office365_connector/fetch_task_doughnut_data',type='json',auth='user')
	def fetch_task_doughnut_data(self, instance_id=1,task_states=[]):
		_logger.info("=========fetch_task_doughnut_data============task_states======================%r",task_states)
		if not task_states:
			string_for_query = "(100000)"
		else:
			string_for_query = '('
			for status in task_states:
				string_for_query += str(status)+","
			string_for_query = string_for_query[0:-1]+ ')'
		data = {'data':{'task_data':{},'task_statuses':[],'color':[]},'total':0}
		# if not len(task_states) > 1:
		# 	return data
		color = ('#1CBC23','#FF5757','#FF8A1F')
		select_sql_clause = """SELECT count(pt.stage_id) as total_stage,pt.stage_id FROM project_task pt inner join
		office365_task_mapping otm on (pt.id = otm.name) where otm.instance_id=%d AND pt.stage_id in  %s
		group by stage_id"""%(instance_id,string_for_query)
		request.env.cr.execute(select_sql_clause)
		query_results = request.env.cr.dictfetchall()
		

		_logger.info("=========fetch_task_doughnut_data==================================%r",query_results)

		count = 0
		total = 0
		for check in query_results:
			name = request.env['project.task.type'].browse(int(check['stage_id'])).name
			data['data']['task_data'][name] = check['total_stage']
			data['data']['color'].append(color[count])
			data['data']['task_statuses'].append(name.capitalize())
			total += check['total_stage']
			count += 1
		_logger.info("=========fetch_sales_doughnut_data==================================%r",data)
		data['total'] = total
		return data

	@http.route('/wk_office365_connector/get_dashboard_line_data',type = 'json', auth = 'user')
	def get_dashboard_line_data(self,instance_id = 1,month=False,contact=True,calendar=True):
		labels = [
				'Mon', 'Tue',
				'Wed', 'Thu', 'Fri',
				'Sat', 'Sun'
			]
		if month:
			query_contact = """
			select to_char(create_date, 'Dy') AS "day",count(*) as total_count
			FROM office365_contact_mapping WHERE to_char(create_date,'Mon') ='%s' AND instance_id = %d
			GROUP BY to_char(create_date, 'Dy')
			"""%(month,instance_id)
			query_calendar = """
			select to_char(create_date, 'Dy') AS "day",count(id) as total_count
			FROM office365_calendar_mapping WHERE to_char(create_date,'Mon') ='%s' AND instance_id = %d
			GROUP BY to_char(create_date, 'Dy')
			"""%(month,instance_id)
		else:
			query_contact = """
			select to_char(create_date, 'Dy') AS "day",count(*) as total_count
			FROM office365_contact_mapping WHERE instance_id = %d
			GROUP BY to_char(create_date, 'Dy')
			"""%instance_id
			query_calendar = """
			select to_char(create_date, 'Dy') AS "day",count(*) as total_count
			FROM office365_calendar_mapping WHERE instance_id = %d
			GROUP BY to_char(create_date, 'Dy')
			"""%instance_id
		data = {'labels':labels,
		'datasets':[]}
		if contact:
			contact_vals = {
                    'label': "Contact",
                    'fill': False,
                    'lineTension': 1,
                    'backgroundColor': "#FFB661",
                    'borderColor': "#5E2160", 
                    'borderCapStyle': False,
                    'borderDash': [],
                    'borderDashOffset': 0.0,
                    'borderJoinStyle': 'miter',
                    'pointBorderColor': "#5E2160",
                    'pointBackgroundColor': "white",
                    'pointBorderWidth': 1,
                    'pointHoverRadius': 8,
                    'pointHoverBackgroundColor': "#5E2160",
                    'pointHoverBorderColor': "#FFB661",
                    'pointHoverBorderWidth': 2,
                    'pointRadius': 4,
                    'pointHitRadius': 10,
                    'data': [],
                    'spanGaps': True,
                  }
			request._cr.execute(query_contact)
			contact_data = {data['day'].strip():data['total_count'] for data in request._cr.dictfetchall()}
			for label in labels:
				contact_vals['data'].append(int(contact_data.get(label,0)))
			data['datasets'].append(contact_vals)
		if calendar:
			calendar_vals = {
                    'label': "Calendar",
                    'fill': False,
                    'lineTension': 1,
                    'backgroundColor': "#201CD9",
                    'borderColor': "#2492E1", 
                    'borderCapStyle': False,
                    'borderDash': [],
                    'borderDashOffset': 0.0,
                    'borderJoinStyle': 'miter',
                    'pointBorderColor': "#201CD9",
                    'pointBackgroundColor': "white",
                    'pointBorderWidth': 1,
                    'pointHoverRadius': 8,
                    'pointHoverBackgroundColor': "#201CD9",
                    'pointHoverBorderColor': "#2492E1",
                    'pointHoverBorderWidth': 2,
                    'pointRadius': 4,
                    'pointHitRadius': 10,
                    'data': [],
                    'spanGaps': True,
                  }
			request._cr.execute(query_calendar)
			calendar_data = {data['day'].strip():data['total_count'] for data in request._cr.dictfetchall()}
			for label in labels:
				calendar_vals['data'].append(int(calendar_data.get(label,0)))
			data['datasets'].append(calendar_vals)
		# _logger.info("============contact_vals===================%r",contact_data)
		return {
			'data':data
		}