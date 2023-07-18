// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Tracker Direct"] = {
  filters: [
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
      options: "Open\nClosed\nAll",
      default: "Open",
    },
    {
      fieldname: "sales_person",
      label: __("Sales Person"),
      fieldtype: "Link",
      options: "Sales Person",
    },
    {
      fieldname: "cost_center",
      label: __("Cost Center"),
      fieldtype: "Link",
      options: "Cost Center",
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
      label: __("UPG"),
      fieldname: "upg",
      fieldtype: "Link",
      options: "Unified Product Group",
      get_query: function () {
        return {
          query:
            "uetl.uetl.report.sales_tracker_direct.sales_tracker_direct.get_upg",
          filters: {
            brand: frappe.query_report.get_filter_value("brand"),
          },
        };
      },
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
    {
      label: "Material Receipt Date",
      fieldname: "mr_date",
      fieldtype: "Select",
      options: "\nYesterday\nToday",
    },
    {
      label: "On Order NP",
      fieldname: "on_order_np_qty",
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
