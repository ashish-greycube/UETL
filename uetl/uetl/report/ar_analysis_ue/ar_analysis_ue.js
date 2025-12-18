// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["AR Analysis UE"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      reqd: 1,
      default: frappe.defaults.get_user_default("Company"),
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
      fieldname: "payment_type",
      label: __("Payment Type"),
      fieldtype: "Select",
      options: __("Incoming") + "\n" + __("Outgoing"),
      default: __("Incoming"),
    },
    {
      fieldname: "party_type",
      label: __("Party Type"),
      fieldtype: "Select",
      options: "Customer",
      default: "Customer",
    },
    {
      fieldname: "party",
      label: __("Party"),
      fieldtype: "Dynamic Link",
      get_options: function () {
        var party_type = frappe.query_report.get_filter_value("party_type");
        var party = frappe.query_report.get_filter_value("party");
        if (party && !party_type) {
          frappe.throw(__("Please select Party Type first"));
        }
        return party_type;
      },
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
