# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe

from erpnext.accounts.report.item_wise_purchase_register.item_wise_purchase_register import (
    execute as _execute,
)
from uetl.uetl.report import csv_to_columns


def execute(filters=None):
    columns, data, *ignore = _execute(filters)
    data = data[:-1]  # remove Totals row
    return get_columns(columns), get_data(data)


def get_columns(columns):
    columns = [
        d
        for d in columns
        if d["fieldname"]
        in (
            "item_code",
            "item_name",
            "item_group",
            "description",
            "invoice",
            "posting_date",
            "supplier_name",
            "stock_qty",
            "rate",
            "stock_uom",
            "amount",
            "purchase_order",
        )
    ]

    addnl_columns = """
Total Cost,total_cost,Currency,,130
Rate(USD),rate_usd,,,130
Amount(USD),amount_usd,,,130
Date Code,date_code,,,130
Country Of Origin,country_of_origin,,,130
Cost Centre,cost_center,,,130
Currency,pr_currency,,,130
Ex Rate,conversion_rate,,,130
Purchase Receipt number,purchase_receipt,,,130
Purchase Receipt Date,pr_date,Date,,130
Batch ID,batch_no,,,130
    """

    return columns + csv_to_columns(addnl_columns)


def get_data(data):
    print(data[:1])

    pr_no = [d.get("purchase_receipt") for d in data]

    pr_data = {
        d.name: d
        for d in frappe.db.sql(
            """
select 
	tpr.name , tpr.currency pr_currency , tpr.conversion_rate , tpr.posting_date pr_date ,
	tpri.rate rate_usd , tpri.amount amount_usd , tpri.date_code_cf , tpri.batch_no ,
	tpri.country_of_origin_cf , tpri.cost_center , tpri.landed_cost_voucher_amount ,
	ts.payment_terms , ts.supplier_group , ts.country 
from `tabPurchase Receipt` tpr 
inner join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name 
inner join tabSupplier ts on ts.name = tpr.supplier 
where tpr.name in ({})
    """.format(
                ", ".join(["%s"] * len(pr_no))
            ),
            tuple(pr_no),
            as_dict=True,
        )
    }

    for d in data:
        d.update(pr_data.get(d.get("purchase_receipt", ""), {}))
        d.update(
            {"total_cost": d.get("amount", 0) + d.get("landed_cost_voucher_amount", 0)}
        )

    return data
