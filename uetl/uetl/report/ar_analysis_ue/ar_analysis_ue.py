# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe

from erpnext.accounts.report.payment_period_based_on_invoice_date.payment_period_based_on_invoice_date import (
    execute as _execute,
)
from uetl.uetl.report.sales_tracker_direct.sales_tracker_direct import csv_to_columns


def execute(filters=None):
    columns, data = _execute(filters)

    col_fields = [d.get("fieldname") for d in columns]
    data = [dict(zip(col_fields, d)) for d in data]

    print(data[:5])

    columns = get_columns(columns)
    if data:
        invoice_data = get_invoice_data(data) or {}

        for d in data:
            if d["invoice"] in invoice_data:
                d.update(invoice_data.get(d["invoice"]))
            print(d.get("delay_in_payment"))

        avg_delay = sum(d.get("delay_in_payment") for d in data) // len(data)
        total_credit = sum(d.get("credit", 0) for d in data)

        last_row = []
        for d in columns:
            if d["fieldname"] == "delay_in_payment":
                last_row.append(avg_delay)
            elif d["fieldname"] == "credit":
                last_row.append(total_credit)
            else:
                last_row.append("")

        data.append(last_row)

    return columns, data


def get_invoice_data(data):
    """update data with data from sales invoice item cost center and sales person"""
    invoices = [d["invoice"] for d in data]

    addnl_data = frappe.db.sql(
        """
select
    tsii.parent sales_invoice,
    tst.sales_person , tsp.parent_sales_person , tsgp.parent_sales_person grand_parent_sales_person ,
    tsii.cost_center , tccp.parent_cost_center , tccgp.parent_cost_center grand_parent_cost_center
from `tabSales Invoice Item` tsii 
    left outer join (
        select parent, sales_person  from `tabSales Team` tst 
        group by parent
    ) tst on tst.parent = tsii.parent
    left outer join `tabSales Person` tsp on tsp.name = tst.sales_person 
    left outer join `tabSales Person` tsgp on tsgp.name = tsp.parent_sales_person  
    left outer JOIN `tabCost Center` tccp on tccp.name = tsii.cost_center 
    left outer JOIN `tabCost Center` tccgp on tccgp.name = tccp.parent_cost_center 
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
        "Cost Center,cost_center,,,150",
        "Sales Person,sales_person,,,150",
        "BU Product Team,grand_parent_cost_center,,<150",
        "BU Product,parent_cost_center,,,150",
        "RSM Team,parent_cost_center,,,150",
        "BU Sales,grand_parent_cost_center,,,150",
    ]

    return columns + csv_to_columns("\n".join(additional_columns))
