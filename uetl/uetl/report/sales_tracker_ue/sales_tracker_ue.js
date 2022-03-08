// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Tracker UE"] = {
	"filters": [
		{
			label: "Display Grouped",
			fieldname: "hide_group_fields",
			fieldtype: "Check",
			default: 1,
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
