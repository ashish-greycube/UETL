// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Inventory Analysis UE"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date on PR"),
      fieldtype: "Date",
      default: frappe.defaults.get_user_default("year_start_date"),
    },
    {
      fieldname: "to_date",
      label: __("To Date on PR"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
    },
    {
      fieldname: "inventory_type",
      label: __("Inventory Type"),
      fieldtype: "Select",
      options: "Sold\nPending\nAll",
      default: "Sold",
    },
    {
      fieldname: "customer",
      label: __("Customer"),
      fieldtype: "Link",
      options: "Customer",
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
  ],
};
