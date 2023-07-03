// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Tracker UE"] = {
  filters: [
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
    },
    {
      label: "Material Receipt Date",
      fieldname: "mr_date",
      fieldtype: "Select",
      options: "\nYesterday\nToday",
    },
    {
      label: "On Order NP",
      fieldname: "on_order_np",
      fieldtype: "Select",
      options: "\n> 0\n= 0",
    },
    {
      label: "Reserved Order Qty",
      fieldname: "reserved_order_qty",
      fieldtype: "Select",
      options: "\n> 0\n= 0",
    },
    {
      label: "Reserved Physical Qty",
      fieldname: "reserved_physical_qty",
      fieldtype: "Select",
      options: "\n> 0\n= 0",
    },
    {
      label: "Sold Qty",
      fieldname: "sold_qty",
      fieldtype: "Select",
      options: "\n> 0\n= 0",
    },
    {
      label: "Pending Qty",
      fieldname: "pending_qty",
      fieldtype: "Select",
      options: "\n> 0\n= 0",
    },
  ],

  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    if (value && column.fieldname == "customer_name") {
      value = `<a href="/app/customer/${data["customer"]}" data-doctype="Customer">${data["customer_name"]}</a>`;
    }
    return value || "";
  },
};
