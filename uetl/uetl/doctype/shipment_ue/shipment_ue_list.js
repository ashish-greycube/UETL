// Copyright (c) 2025, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.listview_settings["Shipment UE"] = {
    refresh: function (listview) {
        listview.toggle_side_bar();
    },

    onload: function (listview) {
        if (listview.page.fields_dict.sales_invoice) {
            listview.page.fields_dict.sales_invoice.get_query = function () {
                return {
                    filters: {
                        gst_category: ["=", "Overseas"],
                    },
                };
            };
        }
    },
}