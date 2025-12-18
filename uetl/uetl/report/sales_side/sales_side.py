# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe

from uetl.uetl.report.sales_personwise_transaction_ue.sales_personwise_transaction_ue import (
    execute as _execute,
)


def execute(filters=None):
    columns, data = _execute(filters)
    data = data[:-1]

    if filters.get("sez_status") == "Pending":
        data = [d for d in data if d.is_pending_sez]
    elif filters.get("sez_status") == "Completed":
        data = [d for d in data if not d.is_pending_sez]

    for d in data:
        d.billing_month = d.posting_date.strftime("%b")

    return get_columns(columns), data


def get_columns(columns):
    return columns + [
        {
            "label": "Billing Month",
            "fieldname": "billing_month",
            "fieldtype": "Data",
            "width": "140",
        },
        # {
        #     "label": "Parent customer name",
        #     "fieldname": "parent_customer_cf",
        #     "fieldtype": "Data",
        #     "width": "140",
        # },
        # {
        #     "label": "Customer ID",
        #     "fieldname": "customer_id_cf",
        #     "fieldtype": "Data",
        #     "width": "140",
        # },
        {
            "label": "Customer Country",
            "fieldname": "country",
            "fieldtype": "Data",
            "width": "140",
        },
        {
            "label": "Requested ship date (CRD)",
            "fieldname": "tsoi_delivery_date",
            "fieldtype": "Date",
            "width": "130",
        },
        {
            "label": "Payment term (Sales)",
            "fieldname": "payment_terms_template",
            "fieldtype": "Link",
            "options": "Payment Term",
            "width": "190",
        },
        {
            "label": "Batch ID",
            "fieldname": "batch_no",
            "fieldtype": "Link",
            "options": "Batch",
            "width": "140",
        },
        {
            "label": "UOM",
            "fieldname": "uom",
            "fieldtype": "Data",
            "width": "140",
        },
        {
            "label": "Purchaser",
            "fieldname": "purchaser_cf",
            "fieldtype": "Data",
            "width": "140",
        },
        {
            "label": "Is SEZ Pending",
            "fieldname": "custom_sez_file_attachment",
            "fieldtype": "Check",
            "width": "90",
        }
    ]
