// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Inventory Analysis UE"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date on PR"),
      fieldtype: "Date",
      // default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
      // default: "2022-04-01",
      hidden: 1
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
      default: "Pending",
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
    {
      fieldname: "warehouse",
      label: __("Warehouse"),
      fieldtype: "Link",
      options: "Warehouse",
    },
  ],
};
