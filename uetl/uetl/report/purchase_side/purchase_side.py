# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe


from india_compliance.gst_india.report.gst_itemised_purchase_register.gst_itemised_purchase_register import (
    execute as _execute,
)
from uetl.uetl.report import csv_to_columns


COLUMNS = (
    "item_code",
    "item_name",
    "item_group",
    "description",
    "invoice",
    "posting_date",
    "purchase_receipt",
    "pr_date",
    "batch_no",
    "supplier_name",
    "supplier_group",
    "supplier_country",
    "supplier_payment_terms",
    "supplier_gstin",
    "gst_hsn_code",
    "bill_no",
    "bill_date",
    "purchase_order",
    "stock_qty",
    "stock_uom",
    "rate",
    "amount",
    "landed_cost_voucher_amount",
    "total_cost",
    "rate_usd",
    "amount_usd",
    "date_code_cf",
    "country_of_origin_cf",
    "pri_cost_center",
    "pr_currency",
    "conversion_rate",
)


def execute(filters=None):
    columns, data, *ignore = _execute(filters)
    # return columns, data

    return get_columns(columns), get_data(data)


def get_columns(columns):
    for col in columns:
        if col["fieldname"] == "Purchase Receipt":
            col["fieldname"] = "purchase_receipt"

    addnl_columns = """
Landed Cost Voucher Amount,landed_cost_voucher_amount,,,130
Total Cost,total_cost,,,130
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
    col_dict = {
        d["fieldname"]: d
        for d in columns + csv_to_columns(addnl_columns)
        if d["fieldname"] in COLUMNS
    }

    return [col_dict[d] for d in COLUMNS if d in col_dict]


def get_data(data):
    pr_no = [d.get("purchase_receipt") for d in data]

    pr_data = {
        d.name: d
        for d in frappe.db.sql(
            """
select 
	tpr.name , tpr.currency pr_currency , tpr.conversion_rate , tpr.posting_date pr_date ,
	tpri.rate rate_usd , tpri.amount amount_usd , tpri.date_code_cf , tpri.batch_no ,
	tpri.country_of_origin_cf , tpri.cost_center pri_cost_centerß, tpri.landed_cost_voucher_amount ,
	ts.payment_terms supplier_payment_terms , ts.supplier_group , ts.country supplier_country
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
            {
                "total_cost": round(
                    d.get("amount", 0) + d.get("landed_cost_voucher_amount", 0), 2
                )
            }
        )

    return data
