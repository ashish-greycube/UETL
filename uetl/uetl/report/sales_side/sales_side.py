# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe

from uetl.uetl.report.sales_personwise_transaction_ue.sales_personwise_transaction_ue import (
    execute as _execute,
)


def execute(filters=None):
    columns, data = _execute(filters)

    data = data[:-1]

    # set additional customer fields
    customers = [d.customer for d in data]
    customer_details = {
        d.customer: d
        for d in frappe.db.sql(
            """
            select name customer from `tabCustomer`
            where name in ({})
    """.format(
                ", ".join(["%s"] * len(customers))
            ),
            tuple(customers),
            as_dict=True,
        )
    }

    for d in data:
        d.update(customer_details.get(d.customer))
        d.billing_month = d.posting_date.strftime("%b")

    # update data from SI, SO
    invoices = [d.name for d in data]
    si_so_details = {
        d.name: d
        for d in frappe.db.sql(
            """
        select 
            tsi.name ,
            batch_no , tsi.payment_terms_template , tsii.item_code , tsii.uom ,
            tsii.sales_order , tsii.so_detail , tsoi.purchaser_cf , tso.delivery_date ,
            ta.country
        from `tabSales Invoice Item` tsii 
        inner join `tabSales Invoice` tsi on tsi.name = tsii.parent 
        left outer join `tabSales Order` tso on tso.name = tsii.sales_order 
        left outer join `tabSales Order Item` tsoi on tsoi.name = tsii.so_detail 
        left outer join tabCustomer tc on tc.name = tsi.customer 
        left outer join tabAddress ta on ta.name = tc.customer_primary_address 
       where tsi.name in ({})
    """.format(
                ", ".join(["%s"] * len(invoices))
            ),
            tuple(invoices),
            as_dict=True,
        )
    }
    for d in data:
        d.update(si_so_details.get(d.name))

    return get_columns(), data


def get_columns():
    return [
        {
            "label": "Billing Month",
            "fieldname": "billing_month",
            "fieldtype": "Data",
            "width": "140",
        },
        {
            "label": "Parent customer name",
            "fieldname": "parent_customer",
            "fieldtype": "Data",
            "width": "140",
        },
        {
            "label": "Customer ID",
            "fieldname": "customer_id",
            "fieldtype": "Data",
            "width": "140",
        },
        {
            "label": "Customer Country",
            "fieldname": "country",
            "fieldtype": "Data",
            "width": "140",
        },
        {
            "label": "Requested ship date (CRD)",
            "fieldname": "delivery_date",
            "fieldtype": "Date",
            "width": "190",
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
            "fieldtype": "Data",
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
    ]
