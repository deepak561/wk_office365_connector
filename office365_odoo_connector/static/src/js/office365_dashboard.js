/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL: <https://store.webkul.com/license.html/> */
odoo.define('office365_odoo_connector.office365.dashboard',function (require) {
	'use strict'

	let AbstractAction = require('web.AbstractAction')
	let ajax = require('web.ajax')
	let core = require('web.core')
    var _t = core._t;
    var relationalFields = require('web.relational_fields');
    var fieldMany2One = relationalFields.FieldMany2One;
    var office365Many2one = fieldMany2One.extend({
        start: function () {
            this.$el.addClass('w-100');
            return this._super.apply(this, arguments);
        }
    });

    var date = new Date();
    console.log("Date",date)
    var mnth = false
    var flag= false

    var months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
      ];

	let office365Dashboard = AbstractAction.extend({
		template: 'office365_dashboard',
		jsLibs: [
			'/web/static/lib/Chart/Chart.js',
        ],
        events: {
            'click .open_instance_form':'open_instance_form',
            'click .wizard_import':'open_wizard_import',
			'click .wizard_export':'open_wizard_export',
			'click .open_mapping_view':'open_mapping_view',
            'change #line_obj_change':'reload_line_graph',
            'change #change_instance':'change_current_instance',
            'click .change_graph':'change_line_graph',
            'click #click_setting':'open_instance_setting',
            'click #click_button':'open_list_view',
		},
        willStart: function () {
            var self = this;
            var superDef = this._super.apply(this, arguments);
            this.instance_id = false;
            self.calendar = true;
            self.contact = true;
            return $.when(
				ajax.loadLibs(this),
				this._super(),
			).then(function(){
				return self.fetch_instance_id()
			}).then(function(){
				return self.fetch_instance_details()
            }).then(function(){
				return self.fetch_instance_extra_details()
            }).then(function(){
                return self.get_dashboard_line_data()
            }).then(function(){
				return self.fetch_task_doughnut_data()
            // }).then(function(){
            //     return self.calender_month_detail()
            })
        },
        start: function(){
            var self = this;
            this._super().then(function () {
                // self.calendar_data()
                self.calender_month_detail()
                self.fetch_calendar_events_details()
                self.fetch_project_details()
                var prev = self.$el.find('.prev')
                var next = self.$el.find('.next')
                var days = self.$el.find('#day')
                var btn_odoo = self.$el.find('#btn_odoo')
                var btn_office365 = self.$el.find('#btn_office365')
                btn_odoo.addClass('btn-info')
                btn_odoo.on('click',function(){
                    btn_office365.removeClass('btn-info')
                    btn_odoo.addClass('btn-info')
                    self.from_calendar = 'export'
                    self.fetch_calendar_events_details()
                    days.empty();
                    self.calender_month_detail()
                })
                btn_office365.on('click',function(){
                    btn_odoo.removeClass('btn-info')
                    btn_office365.addClass('btn-info')
                    self.from_calendar = 'import'
                    self.fetch_calendar_events_details()
                    days.empty();
                    self.calender_month_detail()
                })
                prev.on('click',function(){
                    mnth = date.getMonth() - 1;
                    days.empty();
                    date.setMonth(date.getMonth() - 1);
                    console.log("Clicked:",mnth)
                    self.calender_month_detail()
                    // self.calendar_data()
                })
                next.on('click',function(){
                    mnth = date.getMonth() + 1;
                    days.empty();
                    date.setMonth(date.getMonth() + 1);
                    console.log("Clicked:",mnth)
                    self.calender_month_detail()
                    // self.calendar_data()
                })
            })
        },
        open_instance_setting(ev){
            var self = this;
            self.call_office365_action('office365 Connection Settings', 'office365.instance',
             [], [[false,'form'],[false,'list']],self.instance_id);
		},
		open_mapping_view(ev){
			var self = this;
			var model = ev.currentTarget.id;
			if(model)
				return self.call_office365_action(
				'Mapping',
				 model,
				[['instance_id','=',self.instance_id]],
				[[false,'list'],[false,'form']]);
			
		},

        calender_month_detail(){
            var self = this
            var selected_instance = $('#change_instance option:selected').val()
            console.log('calender_month_detail:',mnth)
			return this._rpc({
                route: '/office365_odoo_connector/calender_month_detail',
                params:{'instance_id':selected_instance,'created_by':self.from_calendar,'month':months[date.getMonth()]}
			}).then(function (result) {
                console.log('calender_month_detail:',result)
                    self.sel_month = result.month;
                    self.sel_date = result.date
                    // if (flag){
                        self.calendar_data()
                    // }
			})
        },

        calendar_data: function(){
            let self = this;
            var lastDay = new Date(
                date.getFullYear(),
                date.getMonth() + 1,
                0
            ).getDate();
            var prevLastDay = new Date(
                date.getFullYear(),
                date.getMonth(),
                0
              ).getDate();
            
              var firstDayIndex = new Date(date.getFullYear(), date.getMonth(), 1).getDay();
            
              
            self.mnth_nm = months[mnth]
            var month_name = self.$el.find('#month_name')
            month_name.html(months[date.getMonth()])
            var days = self.$el.find('#day')
            console.log("calendar_data0",self.sel_date)
            console.log("calendar_data1",self.sel_month)
            console.log("calendar_data2",date.getMonth())

            for (var x = 0; x < firstDayIndex; x++) {
                days.append("<div class='prev_date'></div>");
            }

            for (var i = 1; i <= lastDay; i++) {
                
                if (
                i === new Date().getDate() &&
                date.getMonth() === new Date().getMonth()
                ) {
                    days.append("<div id="+i+"_"+date.getMonth()+" class='today'>"+i+"</div>");
                } else {
                    days.append("<div id="+i+"_"+date.getMonth()+">"+i+"</div>");
                }
                if (self.sel_date.length > 0){
                    $.each(self.sel_date,function(index,value){ 
                        if(date.getMonth() == self.sel_month && i == value){
                            
                            var day_id = (i+"_"+date.getMonth())
                            if (day_id){
                                console.log("calendar_data3",day_id)
                                day_id = '#'+day_id;
                                var evnts = self.$el.find(day_id)
                                evnts.addClass('evnts')
                            }
                        }
                        })
                }
            }

            flag = true
			
		},

        fetch_calendar_events_details(){
            var self = this
            var selected_instance = $('#change_instance option:selected').val()
			return this._rpc({
                route: '/office365_odoo_connector/fetch_calendar_events_details',
                params:{'instance_id':selected_instance,'created_by':self.from_calendar}
			}).then(function (result) {
                var event = self.$el.find('#event')
                event.empty();
                $.each(result,function(index,value){ 
                    console.log(value)
                    // event.append("<div> <img class='icon_normal' src='/office365_odoo_connector/static/src/img/icon_office365.png'/><div style='display:inline-block;'><h6>"+value.name+"</h6><p>"+value.time+" &emsp; "+value.date+"</p></div></div>");
                    event.append("<div class='row'><div class='col-lg-1'><img src='/office365_odoo_connector/static/src/img/icon_office365.png'/></div><div class='col-lg-11'><div style='display:inline-block;'><h6>"+value.name+"</h6><div><p>"+value.time+" &emsp; "+value.date+"</P></div></div></div>");
                    })
			})
        },


        

        fetch_project_details(){
            var self = this
            var selected_instance = $('#change_instance option:selected').val()
			return this._rpc({
                route: '/office365_odoo_connector/fetch_project_details',
                params:{'instance_id':selected_instance}
			}).then(function (result) {
                console.log("fetch_project_details Events:",result)
                var project_stats = self.$el.find('#project_stats')
                $.each(result,function(index,value){ 
                    project_stats.append("<div><p style='display: inline-block;'>"+value.name+"</p><p style='float: right;'>"+value.vals+"</p></div>");
                    })
			})
        },


        change_current_instance(){
            var self = this
            var selected_instance = $('#change_instance option:selected').val()
			return this._rpc({
                route: '/office365_odoo_connector/change_instance_id',
                params:{'instance_id':selected_instance}
			}).then(function (result) {
                self.instance_id = result.instance_id
                location.reload(true)
			})
        },
        on_attach_callback () {
            // this.render_line_graph()
            // this.render_sale_graph()
            let self = this
            console.log('self.task_states',self.task_states)
            // if(self.task_states.length < 3){
            //     var msg = self.$el.find('#office365_task_msg')
            //     msg.append("<p style='text-align: center;'>"+'Please Select 3 States of Task from the setting!'+"</p>");
            //     console.log('msg',msg)
            // }
            // else{
                this._chartRegistry()
                this.render_task_graph()

            // }
        },
        fetch_task_doughnut_data () {
			let self = this
            console.log('fetch_task_doughnut_data task_states',self.task_states)
			return this._rpc({
				route: '/office365_odoo_connector/fetch_task_doughnut_data',
				params: {'instance_id':self.instance_id,'task_states':self.task_states}
			}).then(function (result) {
                console.log("fetch_task_doughnut_data: ",result)
                var res = ''
                res = result.data
				self.task_data = res.task_data
				self.task_statuses = res.task_statuses
				self.task_color = res.color
                self.task_msg =('Total Task \n').concat(result.total.toString())
			})
        },

        open_list_view(ev){
			let self = this;
			var domain = [];
			var view_type = [[false,'list'],[false,'form']];
			var model = false;
			var name = 'Office 365 Project Mapping';
			model = 'office365.project.mapping'
			return self.call_office365_action(name, model, domain, view_type);
		},
        render_task_graph () {
			let self = this;
			$('#office365_task').replaceWith($('<canvas/>',{id:'office365_task'}))
			self.chart = new Chart('office365_task',{
				type: 'doughnut',
				data: {
					labels: self.task_statuses,
					datasets: [{
						data: Object.values(self.task_data),
						backgroundColor:self.task_color
					}],
				},
				options: {
                    responsive:true,
					maintainAspectRatio: false,
					legend: {
						display:true,
                        position: 'right',
                        align: 'start',
                        labels:{
                            usePointStyle:true
                        },
					},
					cutoutPercentage:80,
					elements:{
						center: {
							text: _t(self.task_msg),
						}
					},
					onClick (e,i){
                        if (i.length) {
                            var state = i[0]['_view']['label']
                            state =  state.toLowerCase();
                            self.call_office365_action(
                                'Project Task Mapping',
                                'office365.task.mapping',
                                [['name.stage_id.name','ilike',state],
                                ['instance_id','=',self.instance_id]],
                                [[false,'list'],[false,'form']]

                            )
                            console.log("")
                        }
                    },
				},
			});
		},

        _chartRegistry: function () {
			Chart.pluginService.register({
			  beforeDraw: function (chart) {
				if (chart.config.options.elements.center) {
				  var ctx = chart.chart.ctx;
				  var centerConfig = chart.config.options.elements.center;
				  var txt = centerConfig.text;
				  var color = '#555555';
				  var sidePadding = centerConfig.sidePadding || 30;
				  var sidePaddingCalculated = (sidePadding/100) * (chart.innerRadius * 2);
				  ctx.font = "15px Montserrat";
				  var stringWidth = ctx.measureText(txt).width;
				  var elementWidth = (chart.innerRadius * 2) - sidePaddingCalculated;
				  var widthRatio = elementWidth / stringWidth;
				  var newFontSize = Math.floor(30 * widthRatio);
				  var elementHeight = (chart.innerRadius * 2);
				  var fontSizeToUse = Math.min(newFontSize, elementHeight);
				  ctx.textAlign = 'center';
				  ctx.textBaseline = 'middle';
				  ctx.overflow = 'hidden';
				  var centerX = ((chart.chartArea.left + chart.chartArea.right) / 2);
				  var centerY = ((chart.chartArea.top + chart.chartArea.bottom) / 2);
				  ctx.fillStyle = color;
				  ctx.shadowColor = '#FFFFFF';
				  ctx.shadowBlur = 25;
				  ctx.shadowOffsetX = 2;
				  ctx.shadowOffsetY = 2;
				  ctx.fillText(txt, centerX, centerY);
				}
			  },
			});
		  },


        get_dashboard_line_data(month=false){
            let self = this;
			return this._rpc({
				route:'/office365_odoo_connector/get_dashboard_line_data',
                params:{'instance_id':self.instance_id,
            'month':month,
            'contact':self.contact,
            'calendar':self.calendar}
			}).then(function(result){
                self.line_data = result.data
                console.log("get_dashboard_line_data",result)
            });
        },
        open_wizard_import(ev){
            let self = this;
			return this._rpc({
				route:'/office365_odoo_connector/get_synchronisation_id',
                params:{
            action:'import',
            'instance':self.instance_id}
			}).then(function(result){
                var id = result.id;
                return self.call_office365_action('Bulk Synchronisation', 'office365.bulk.synchronisation', 
                [], [[false,'form']], id,true,'new');
            });

        },
        open_wizard_export(ev){
            let self = this;
			return this._rpc({
				route:'/office365_odoo_connector/get_synchronisation_id',
                params:{action:'export',
            'instance':self.instance_id}
			}).then(function(result){
                var id = result.id;
                return self.call_office365_action('Bulk Synchronisation', 'office365.bulk.synchronisation', 
                [], [[false,'form']], id,true,'new');
            });
        },
        open_instance_form(ev){
			var action_id = parseInt(ev.currentTarget.dataset['id']);
			let self = this;
			var domain = [];
			var view_type = [[false,'form'],[false,'list']];
			var model = 'office365.instance';
			return self.call_office365_action('office365 Instance', model, domain, view_type,action_id);

		},
        fetch_instance_extra_details(){
            let self = this;
			return this._rpc({
                route: '/office365_odoo_connector/fetch_instance_extra_details',
                params:{instance_id:self.instance_id}
			}).then(function (result) {
				self.extra_data = result.data
                self.contact_count = result.data.contact.count
                self.odoo_contact = result.odoo_contact
                self.office_contact = result.data.contact.count - result.odoo_contact
                // self.contact_count = 0
                // self.odoo_contact = 0
                // self.office_contact = 0
                console.log("fetch_instance_extra_details",result)
			})

        },
        fetch_instance_id () {
			let self = this;
			return this._rpc({
				route: '/office365_odoo_connector/fetch_instace_id'
			}).then(function (result) {
                self.instance_id = result.instance_id
                self.current_date = result.current_date
                self.task_states = result.task_states
			})
        },
        call_office365_action(name, res_model, domain, view_type, res_id=false,nodestroy=false,target='self'){
			let self = this;
			return self.do_action({
				name: name,
				type: 'ir.actions.act_window',
				res_model: res_model,
				views: view_type,
				domain:domain,
				res_id:res_id,
				nodestroy: nodestroy,
				target: target,	
			});
		},
        fetch_instance_details(){
            let self = this;
			return this._rpc({
				route: '/office365_odoo_connector/fetch_instace_details'
			}).then(function (result) {
                self.selection_instance = result
                console.log(self.selection_instance)
			})
        },
        _createMany2One: function (name, model, value,domain, context) {
            var fields = {};
            fields[name] = {type: 'many2one', relation: model, string: name};
            var data = {};
            data[name] = {data: {display_name: value}};
            var record = {
                id: name,
                res_id: 1,
                model: 'dummy',
                fields: fields,
                fieldsInfo: {
                    default: fields,
                },
                data: data,
                getDomain: domain || function () { return []; },
                getContext: context || function () { return {}; },
            };
            var options = {
                mode: 'edit',
                noOpen: true,
                attrs: {
                    can_create: false,
                    can_write: false,
                }
            };
            return new office365Many2one(this, name, record, options);
        },
	})
	core.action_registry.add('office365_dashboard',office365Dashboard)
})
