// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Tracker Direct"] = {
	"filters": [
		{
			label: "Show Summary",
			fieldname: "hide_group_fields",
			fieldtype: "Check",
			default: 0,
		},
		{
			label: "Sales Order Status",
			fieldname: "so_status",
			fieldtype: "Select",
			options: "All\nOpen\nClosed",
			default: "All",
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person"
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center"
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "brand",
			label: __("Brand"),
			fieldtype: "Link",
			options: "Brand",
		},
		{
			fieldname: "upg",
			label: __("UPG"),
			fieldtype: "Select",
			options: ""
		},
		// {
		// 	fieldname: "status",
		// 	label: __("Status"),
		// 	fieldtype: "Select",
		// 	options: "Order\nDelivery\nBilling"
		// },
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},

	],


	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (value && column.fieldname == "customer_name") {
			value = `<a href="/app/customer/${data['customer']}" data-doctype="Customer">${data['customer_name']}</a>`;
		}
		return value || '';
	},
};
