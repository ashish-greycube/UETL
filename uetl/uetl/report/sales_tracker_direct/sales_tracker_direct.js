// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Tracker Direct"] = {
	"filters": [
		{
			label: "Show Summary",
			fieldname: "hide_group_fields",
			fieldtype: "Check",
			default: 1,
		},
		{
			label: "Sales Order Status",
			fieldname: "so_status",
			fieldtype: "Select",
			options: "All\nOpen\nClosed",
			default: "All",
		}
	],


	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (value && column.fieldname == "customer_name") {
			value = `<a href="/app/customer/${data['customer']}" data-doctype="Customer">${data['customer_name']}</a>`;
		}
		return value || '';
	},
};
