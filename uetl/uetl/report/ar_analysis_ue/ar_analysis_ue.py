# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe

from erpnext.accounts.report.payment_period_based_on_invoice_date.payment_period_based_on_invoice_date import (
    execute as _execute,
)
from uetl.uetl.report.sales_tracker_direct.sales_tracker_direct import csv_to_columns


def execute(filters=None):
    columns, data = _execute(filters)

    if data:
        col_fields = [d.get("fieldname") for d in columns]
        data = [dict(zip(col_fields, d)) for d in data]
        invoice_data = get_invoice_data(data) or {}

        for d in data:
            if d["invoice"] in invoice_data:
                d.update(invoice_data.get(d["invoice"]))

    columns = get_columns(columns)
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
        debug=True,
    )

    return {d.sales_invoice: d for d in addnl_data}


def get_columns(columns):
    """Drop columns not needed and add new columns"""
    columns = [
        d
        for d in columns
        if not d["fieldname"]
        in (
            "payment_document_type",
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
