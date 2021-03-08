/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL: <https://store.webkul.com/license.html/> */
odoo.define('wk_office365_connector.office365.dashboard',function (require) {
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
            'click #click_setting':'open_instance_setting'
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
            // })
            // }).then(function(){
			// 	return self.fetch_task_doughnut_data()
            // })
            // }).then(function(){
			// 	return self.fetch_sales_doughnut_data()
            // })
            }).then(function(){
                self.calendar_data()
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

        calendar_data(ev){
            let self = this;
            var lastDay = new Date(
                date.getFullYear(),
                date.getMonth() + 1,
                0
            ).getDate();
            console.log("lastDay",lastDay)
            var prevLastDay = new Date(
                date.getFullYear(),
                date.getMonth(),
                0
              ).getDate();
              console.log("prevLastDay",prevLastDay)
            
              var firstDayIndex = date.getDay();
              console.log("firstDayIndex",firstDayIndex)
            
            
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
            $(".month p").html(months[date.getMonth()]);

            // var days = self.$el.find('#day')
            var days = $("#day")

            for (var x = 0; x < firstDayIndex; x++) {
                days.append("<div>"+" &emsp; "+"</div>");
            }

            for (var i = 1; i <= lastDay; i++) {
                if (
                i === new Date().getDate() &&
                date.getMonth() === new Date().getMonth()
                ) {
                    days.append("<div class='today'>"+i+"</div>");
                } else {
                    days.append("<div>"+i+"</div>");
                }
            }
			
		},

        change_current_instance(){
            var self = this
            var selected_instance = $('#change_instance option:selected').val()
			return this._rpc({
                route: '/wk_office365_connector/change_instance_id',
                params:{'instance_id':selected_instance}
			}).then(function (result) {
                self.instance_id = result.instance_id
                location.reload(true)
			})
        },
        on_attach_callback () {
            this.render_line_graph()
            // this.render_sale_graph()
            // this.render_purchase_graph()
        },
        fetch_task_doughnut_data () {
			let self = this
			return this._rpc({
				route: '/wk_office365_connector/fetch_task_doughnut_data',
				params: {'instance_id':self.instance_id}
			}).then(function (result) {
                console.log("fetch_task_doughnut_data: ",result)
				// self.purchase_data = result.purchase_data
				// self.purchase_statuses = result.purchase_statuses
				// self.purchase_colors = result.color
			})
        },
        // fetch_sales_doughnut_data () {
		// 	let self = this
		// 	return this._rpc({
		// 		route: '/wk_office365_connector/fetch_sales_doughnut_data',
		// 		params: {'instance_id':self.instance_id}
		// 	}).then(function (result) {
		// 		self.sale_data = result.sale_data
		// 		self.sale_statuses = result.sale_statuses
		// 		self.sale_colors = result.color
		// 	})
		// },
        // render_sale_graph () {
		// 	let self = this;
		// 	$('#office365_sale_order').replaceWith($('<canvas/>',{id:'office365_sale_order'}))
		// 	self.chart = new Chart('office365_sale_order',{
		// 		type: 'doughnut',
		// 		data: {
		// 			labels: self.sale_statuses,
		// 			datasets: [{
		// 				data: Object.values(self.sale_data),
		// 				backgroundColor:self.sale_colors
		// 			}],
		// 		},
		// 		options: {
        //             responsive:true,
        //             cutoutPercentage:60,
        //             maintainAspectRatio: false,
        //             title: {
        //                 display: false,
        //                 text: 'Sale Order',
        //                 fontSize: 15,
        //             },
		// 			legend: {
        //                 display:true,
        //                 position: 'right',
        //                 labels:{
        //                     usePointStyle:true
        //                 },
		// 			},
		// 			onClick (e,i){
		// 				if (i.length) {
		// 					var state = i[0]['_view']['label']
		// 					state =  state.toLowerCase();
		// 					self.call_office365_action(
		// 						'Order Mapping',
		// 						'office365.order',
        //                         [['name.state','=',state],
        //                         ['instance_id','=',self.instance_id]],
		// 						[[false,'list'],[false,'form']]

		// 					)
		// 				}
		// 			},
		// 		},
		// 	});
        // },
        // render_purchase_graph () {
		// 	let self = this;
		// 	$('#office365_task').replaceWith($('<canvas/>',{id:'office365_task'}))
		// 	self.chart = new Chart('office365_task',{
        //         type: 'doughnut',
		// 		data: {
		// 			labels: self.purchase_statuses,
		// 			datasets: [{
		// 				data: Object.values(self.purchase_data),
		// 				backgroundColor:self.purchase_colors
		// 			}],
        //         },
		// 		options: {
        //             responsive:true,
        //             maintainAspectRatio: false,
        //             cutoutPercentage:60,
        //             title: {
        //                 display: false,
        //                 text: 'Purchase Order',
        //                 fontSize: 15,
        //             },
		// 			legend: {
        //                 display:true,
        //                 position: 'right',
        //                 labels:{
        //                     usePointStyle:true
        //                 },
        //             },
		// 			onClick (e,i){
		// 				if (i.length) {
		// 					var state = i[0]['_view']['label']
		// 					state =  state.toLowerCase();
		// 					self.call_office365_action(
		// 						'Purchase Order Mapping',
		// 						'office365.purchase.order',
        //                         [['name.state','=',state],
        //                         ['instance_id','=',self.instance_id]],
		// 						[[false,'list'],[false,'form']]

		// 					)
		// 				}
		// 			},
		// 		},
		// 	});
		// },
        change_line_graph(ev){
            var self = this;
            var id = ev.currentTarget.id;
            if(id=='contact'){
                if(self.contact==false){
                    self.contact=true;
                    $(ev.currentTarget).css('textDecoration','none');
                }else{
                    self.contact=false;
                    $(ev.currentTarget).css('textDecoration','line-through');
                }
            }else{
                if(self.calendar==false){
                    self.calendar=true;
                    $(ev.currentTarget).css('textDecoration','none');
                }else{
                    self.calendar=false;
                    $(ev.currentTarget).css('textDecoration','line-through');
                }
            }
            return $.when().then(function(){
                return self.reload_line_graph()
            })
        },
        reload_line_graph () {
			var self = this
            var selected_option = $('#line_obj_change option:selected').val()
            if(selected_option=='zero')
                selected_option = false;
            return $.when().then(function(){
                return self.get_dashboard_line_data(selected_option)
            }).then(function(){
                return self.render_line_graph()
            })
        },
        render_line_graph () {
			$('#line_chart').replaceWith($('<canvas/>',{id: 'line_chart'}))
            var self = this
            var data = self.line_data;
            var options= {
                maintainAspectfirefoxRatio: false,
                legend: {
                    display: false,
                },
                scales: {
                    xAxes: [{
                        gridLines: {
                            display: false,
                        },
                    }],
                    yAxes: [{
                        gridLines: {
                            display: false,
                        },
                        ticks: {
                            precision: 0,
                        },
                    }],
                },
        };
        var myBarChart = new Chart('line_chart', {
        type: 'line',
        data: data,
        options: options
        }); 
		},
        get_dashboard_line_data(month=false){
            let self = this;
			return this._rpc({
				route:'/wk_office365_connector/get_dashboard_line_data',
                params:{'instance_id':self.instance_id,
            'month':month,
            'contact':self.contact,
            'calendar':self.calendar}
			}).then(function(result){
                self.line_data = result.data
            });
        },
        open_wizard_import(ev){
            let self = this;
			return this._rpc({
				route:'/wk_office365_connector/get_synchronisation_id',
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
				route:'/wk_office365_connector/get_synchronisation_id',
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
                route: '/wk_office365_connector/fetch_instance_extra_details',
                params:{instance_id:self.instance_id}
			}).then(function (result) {
				self.extra_data = result
			})

        },
        fetch_instance_id () {
			let self = this;
			return this._rpc({
				route: '/wk_office365_connector/fetch_instace_id'
			}).then(function (result) {
                self.instance_id = result.instance_id
                self.current_date = result.current_date
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
				route: '/wk_office365_connector/fetch_instace_details'
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
