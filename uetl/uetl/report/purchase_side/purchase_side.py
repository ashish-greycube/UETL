# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.report.item_wise_purchase_register.item_wise_purchase_register import (
    _execute,
)


def execute(filters=None):
    columns, data, *others = _execute(
        filters,
        additional_table_columns=[
            dict(
                fieldtype="Data",
                label="Supplier GSTIN",
                fieldname="supplier_gstin",
                width=120,
            ),
            dict(
                fieldtype="Data",
                label="Company GSTIN",
                fieldname="company_gstin",
                width=120,
            ),
            dict(
                fieldtype="Check",
                label="Is Reverse Charge",
                fieldname="is_reverse_charge",
                width=120,
            ),
            dict(
                fieldtype="Data",
                label="GST Category",
                fieldname="gst_category",
                width=120,
            ),
            dict(
                fieldtype="Data", label="HSN Code", fieldname="gst_hsn_code", width=120
            ),
            dict(
                fieldtype="Data",
                label="Supplier Invoice No",
                fieldname="bill_no",
                width=120,
            ),
            dict(
                fieldtype="Date",
                label="Supplier Invoice Date",
                fieldname="bill_date",
                width=100,
            ),
        ],
        additional_query_columns=[
            "supplier_gstin",
            "company_gstin",
            "is_reverse_charge",
            "gst_category",
            "gst_hsn_code",
            "bill_no",
            "bill_date",
            "pr_detail",
        ],
    )

    columns = get_columns(columns)

    data = get_data(data, filters)

    return columns, data


from uetl.uetl.report import csv_to_columns


COLUMNS = (
    "item_code",
    "item_name",
    "item_group",
    "brand",
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
    "po_posting_date",
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
    "pri_parent_cost_center",
    "pri_grand_parent_cost_center",
    "pr_currency",
    "conversion_rate",
)


def get_columns(columns):
    for col in columns:
        if col["fieldname"] == "Purchase Receipt":
            col["fieldname"] = "purchase_receipt"

    addnl_columns = """
Landed Cost Voucher Amount,landed_cost_voucher_amount,Currency,,130
Total Cost,total_cost,Currency,,130
Rate(USD),rate_usd,,,130
Amount(USD),amount_usd,,,130
Date Code,date_code_cf,,,130
Country Of Origin,country_of_origin_cf,,,130
Cost Centre,pri_cost_center,,,130
Currency,pr_currency,,,130
Ex Rate,conversion_rate,,,130
Purchase Receipt number,purchase_receipt,Link,Purchase Receipt,130
Purchase Receipt Date,pr_date,Date,,130
Purchase Order Date,po_posting_date,Date,,130
Batch ID,batch_no,Link,Batch,130
Supplier Group,supplier_group,,,130
Supplier Payment Terms,supplier_payment_terms,,,180
Item Brand,brand,,,130
BU Product,pri_parent_cost_center,,130
BU Product Team,pri_grand_parent_cost_center,,,130
    """
    col_dict = {
        d["fieldname"]: d
        for d in columns + csv_to_columns(addnl_columns)
        if d["fieldname"] in COLUMNS
    }

    return [col_dict[d] for d in COLUMNS if d in col_dict]


def get_data(data, filters):
    pr_details = [d.get("pr_detail") for d in data]

    pr_data = {
        d.pr_detail: d
        for d in frappe.db.sql(
            """
select 
	tpr.name , tpr.currency pr_currency , tpr.conversion_rate , tpr.posting_date pr_date ,
	tpri.name pr_detail, tpri.rate rate_usd , tpri.amount amount_usd , tpri.date_code_cf , tpri.batch_no ,
	tpri.country_of_origin_cf , tpri.cost_center pri_cost_center, tpri.landed_cost_voucher_amount ,
	ts.payment_terms supplier_payment_terms , ts.supplier_group , ts.country supplier_country ,
    tpo.transaction_date po_posting_date , ti.brand ,
    tccp.parent_cost_center pri_parent_cost_center, 
    tccgp.parent_cost_center pri_grand_parent_cost_center
from `tabPurchase Receipt` tpr 
inner join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name 
inner join `tabItem` ti on ti.name = tpri.item_code
inner join tabSupplier ts on ts.name = tpr.supplier 
inner join `tabPurchase Order` tpo on tpo.name = tpri.purchase_order
left outer JOIN `tabCost Center` tccp on tccp.name = tpri.cost_center 
left outer JOIN `tabCost Center` tccgp on tccgp.name = tccp.parent_cost_center 
where tpri.name in ({})
    """.format(
                ", ".join(["%s"] * len(pr_details))
            ),
            tuple(pr_details),
            as_dict=True,
        )
    }

    for d in data:
        d.update(pr_data.get(d.get("pr_detail", ""), {}))
        d.update(
            {
                "total_cost": round(
                    d.get("amount", 0) + d.get("landed_cost_voucher_amount", 0), 2
                )
            }
        )

    if filters.get("supplier_group"):
        data = [
            d for d in data if d.get("supplier_group") == filters.get("supplier_group")
        ]

    return data
