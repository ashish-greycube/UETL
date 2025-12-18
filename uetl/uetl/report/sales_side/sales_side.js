// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Side"] = {
  filters: [
    {
      fieldname: "sales_person",
      label: __("Sales Person"),
      fieldtype: "Link",
      options: "Sales Person",
    },
    {
      fieldname: "doc_type",
      label: __("Document Type"),
      fieldtype: "Select",
      options: "Sales Invoice",
      default: "Sales Invoice",
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.defaults.get_global_default("year_start_date"),
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
    },
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
    },
    {
      fieldname: "item_group",
      label: __("Item Group"),
      fieldtype: "Link",
      options: "Item Group",
    },
    {
      fieldname: "brand",
      label: __("Brand"),
      fieldtype: "Link",
      options: "Brand",
    },
    {
      fieldname: "customer",
      label: __("Customer"),
      fieldtype: "Link",
      options: "Customer",
    },
    {
      fieldname: "territory",
      label: __("Territory"),
      fieldtype: "Link",
      options: "Territory",
    },
    {
      fieldname: "show_return_entries",
      label: __("Show Return Entries"),
      fieldtype: "Check",
      default: 0,
    },
    {
      fieldname: "cost_center",
      label: __("Cost Center"),
      fieldtype: "Link",
      options: "Cost Center",
    },
    {
      fieldname: "sez_status",
      label: __("SEZ Status"),
      fieldtype: "Select",
      default: 'All',
      width: "120px",
      options: "All\nPending\nCompleted"
    },
  ],

  onload: function () {
    let fiscal_year = erpnext.utils.get_fiscal_year(frappe.datetime.get_today());

    frappe.model.with_doc("Fiscal Year", fiscal_year, function (r) {
      var fy = frappe.model.get_doc("Fiscal Year", fiscal_year);
      frappe.query_report.set_filter_value({
        from_date: fy.year_start_date,
      });
    });
  },
};
