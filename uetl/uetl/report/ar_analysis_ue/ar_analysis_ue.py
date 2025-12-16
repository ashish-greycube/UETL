# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import date_diff

from erpnext.accounts.report.payment_period_based_on_invoice_date.payment_period_based_on_invoice_date import (
    execute as _execute,
)
from uetl.uetl.report.sales_tracker_direct.sales_tracker_direct import csv_to_columns


def execute(filters=None):
    columns, data = _execute(filters)

    col_fields = [d.get("fieldname") for d in columns]
    data = [dict(zip(col_fields, d)) for d in data]

    columns = get_columns(columns)
    if data:
        invoice_data = get_invoice_data(data) or {}

        for d in data:
            if d["invoice"] in invoice_data:
                d.update(invoice_data.get(d["invoice"]))

            if d.get("posting_date") and d.get("invoice_posting_date"):
                d["sales_invoice_delay"] = date_diff(
                    d.get("posting_date"), d.get("invoice_posting_date")
                )
        data = remove_cancelled_payment_entries(data)
        data.append(get_totals(columns, data))

    return columns, data


def remove_cancelled_payment_entries(data):
    """filter out cancelled Payment Entries, till issue is fixed in Erpnext payment_period_based_on_invoice_date"""
    cancelled = frappe.db.sql_list(
        "select name from `tabPayment Entry` where docstatus = 2"
    )
    return [d for d in data if not d["payment_entry"] in cancelled]


def get_totals(columns, data):
    last_row = []
    for d in columns:
        if d["fieldname"] == "delay_in_payment":
            last_row.append(
                sum(d.get("delay_in_payment", 0) for d in data) // len(data)
            )
        elif d["fieldname"] == "credit":
            last_row.append(sum(d.get("credit", 0) for d in data))
        elif d["fieldname"] == "sales_invoice_delay":
            last_row.append(
                sum(d.get("sales_invoice_delay", 0) for d in data) // len(data)
            )
        else:
            last_row.append("")
    return last_row


def get_invoice_data(data):
    """update data with data from sales invoice item cost center and sales person"""
    invoices = [d["invoice"] for d in data]

    addnl_data = frappe.db.sql(
        """
select
    tsii.parent sales_invoice, tsi.payment_terms_template , 
    tst.sales_person , tsp.parent_sales_person , tsgp.parent_sales_person grand_parent_sales_person ,
                -- custom columns from Customer
    tc.custom_line_of_business , 
    tc.custom_potential , 
    tc.parent_customer_name_cf ,
    tc.customer_id_cf ,
    tc.custom_customer_group_company ,
    tc.custom_tier
from `tabSales Invoice Item` tsii 
    inner join `tabSales Invoice` tsi on tsi.name = tsii.parent
    inner join `tabCustomer` tc on tc.name = tsi.customer
    left outer join (
        select parent, sales_person  from `tabSales Team` tst 
        group by parent
    ) tst on tst.parent = tsii.parent
    left outer join `tabSales Person` tsp on tsp.name = tst.sales_person 
    left outer join `tabSales Person` tsgp on tsgp.name = tsp.parent_sales_person  
where tsii.parent in ({})
    """.format(
            ", ".join(["%s"] * len(invoices))
        ),
        tuple(invoices),
        as_dict=True,
    )

    return {d.sales_invoice: d for d in addnl_data}


def get_columns(columns):
    """Drop columns not needed and add new columns"""
    columns = [
        d
        for d in columns
        if not d["fieldname"]
        in (
            "payment_document",
            "party_type",
            "debit",
            "age",
            "range1",
            "range2",
            "range3",
            "range4",
            "remarks",
        )
    ]

    additional_columns = [
        "Sales Person,sales_person,,,150",
        "RSM Team,parent_sales_person,,,150",
        "BU Sales,grand_parent_sales_person,,,150",
        "Payment Terms,payment_terms_template,,,180",
        "Line Of Business,custom_line_of_business,Data,,140",
        "Potential,custom_potential,Data,,140",
        "Parent Customer,parent_customer_name_cf,Data,,140",
        "Customer ID,customer_id_cf,Data,,140",
        "Customer Group Company,custom_customer_group_company,Data,,140",
        "Tier,custom_tier,Data,,140 ",
    ]

    out = []

    for d in columns:
        out.append(d)
        if d["fieldname"] == "delay_in_payment":
            out.append(
                {
                    "fieldname": "sales_invoice_delay",
                    "label": "Delay based on Invoice Date (Days)",
                    "fieldtype": "Int",
                    "width": 130,
                }
            )
    return out + csv_to_columns("\n".join(additional_columns))
