# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, date_diff
from erpnext import get_default_currency

from uetl.uetl.report import csv_to_columns


def execute(filters=None):
    filters["today"] = today()

    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_columns(filters):
    columns = """
    Customer,customer,Link/Customer,,140
    Item Code,item_code,Link/Item,,200
    Item Name,item_name,,,200
    Item Group,item_group,,,130
    Brand,brand,,,130
    Batch,batch_id,Link,Batch,110
    Supplier,supplier,,,120
    Purchase Receipt,reference_name,Link/Purchase Receipt,,130
    Purchase Receipt Date,pr_date,Date,,130
    Received Qty,received_stock_qty,Float,,130
    Sold Qty,sold_qty,Float,,130
    Sold Rate,sold_rate,Currency,,120
    Sold Amount,sold_amount,Currency,,120
    Batch Balance Qty,batch_qty,Float,,130
    Sold Date,dn_date,Date,,120
    Age (in Days),age_in_days,Int,,130
    Batch Balance Age (in Days),batch_balance_age,Int,,130
    Rate,base_rate,Currency,,130
    Batch Amount({}),batch_amount,Currency,,130
    Cost Center,cost_center,,,130
    Purchaser,purchaser_cf,,,120
    Sales Person,sales_person,,,150
    BU Product Team,grand_parent_cost_center,,<150
    BU Product,parent_cost_center,,,150
    RSM Team,parent_sales_person,,,150
    BU Sales,grand_parent_sales_person,,,150
    """.format(
        get_default_currency()
    )
    columns = csv_to_columns(columns)
    if filters.inventory_type == "Sold":
        columns = [d for d in columns if not d["fieldname"] == "batch_balance_age"]
    return columns


def get_data(filters):
    dn_so = frappe.db.sql(
        """
    select dn_so.* ,
        tsp.parent_sales_person , tsgp.parent_sales_person grand_parent_sales_person ,
        tccp.parent_cost_center , tccgp.parent_cost_center grand_parent_cost_center 
    from
    (
		select tdni.batch_no , tdni.item_code , 
        tsoi.cost_center , tsoi.purchaser_cf , tst.sales_person ,
        max(tdn.posting_date) dn_date , sum(tdni.stock_qty) sold_qty ,
        avg(tdni.base_rate) sold_rate , sum(tdni.stock_qty * tdni.base_rate) sold_amount
     	from `tabDelivery Note Item` tdni
     	inner join `tabDelivery Note` tdn on tdn.name = tdni.parent
     	left outer join `tabSales Order Item` tsoi on tsoi.name = tdni.so_detail 
     		and tsoi.parent = tdni.against_sales_order
            and tsoi.docstatus = 1
	    left outer join (
	        select parent, sales_person  from `tabSales Team` tst 
	        where parenttype = 'Sales Order'
	        group by parent
	    ) tst on tst.parent = tsoi.parent     		
     	where tdn.docstatus = 1 and nullif(tdni.batch_no,'') is not null
     	group by tdni.batch_no , tdni.item_code , tdn.customer ,
     	tsoi.cost_center , tsoi.purchaser_cf , tst.sales_person
	) dn_so
    left outer join `tabSales Person` tsp on tsp.name = dn_so.sales_person 
    left outer join `tabSales Person` tsgp on tsgp.name = tsp.parent_sales_person  
    left outer JOIN `tabCost Center` tccp on tccp.name = dn_so.cost_center 
    left outer JOIN `tabCost Center` tccgp on tccgp.name = tccp.parent_cost_center 
                          """,
        as_dict=True,
    )
    dn_so = {(d.batch_no, d.item_code): d for d in dn_so}

    batch_data = frappe.db.sql(
        """
    select 
	    ti.item_code , ti.item_name , ti.item_group , ti.brand ,
        tb.batch_id , tb.supplier , tb.reference_doctype , tb.reference_name , tb.batch_qty ,
        tpr.posting_date pr_date , tpri.received_stock_qty , 
        tpri.base_rate , tb.batch_qty * tpri.base_rate batch_amount ,
        tso.customer
        from tabBatch tb 
    inner join tabItem ti on ti.name = tb.item 
    left outer join `tabPurchase Receipt` tpr on tpr.name = tb.reference_name 
        and tpr.docstatus = 1
    left outer join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name
        and tpri.item_code = tb.item and tpri.batch_no = tb.name
    left outer join `tabSales Order` tso on tso.name = tpri.sales_order_cf
    {}
    """.format(
            get_conditions(filters)
        ),
        filters,
        as_dict=True,
    )

    for d in batch_data:
        d.update(dn_so.get((d.batch_id, d.item_code), {}))
        # age in days
        if not d.batch_qty or d.sold_qty:
            d["age_in_days"] = date_diff(d.dn_date, d.pr_date)
        else:
            d["age_in_days"] = date_diff(today(), d.pr_date)
        # batch_balance_age
        if d.batch_qty:
            d["batch_balance_age"] = date_diff(today(), d.pr_date)

    return apply_filters(batch_data, filters)


def apply_filters(data, filters):
    if filters.customer:
        data = [d for d in data if d.customer == filters.customer]
    if filters.cost_center:
        data = [d for d in data if d.cost_center == filters.cost_center]
    if filters.sales_person:
        data = [d for d in data if d.sales_person == filters.sales_person]
    if filters.inventory_type == "Sold":
        data = [d for d in data if d.sold_qty and not d.batch_qty]
    if filters.inventory_type == "Pending":
        data = [d for d in data if d.batch_qty]

    return data


def get_conditions(filters):
    conditions = []

    if filters.from_date:
        conditions.append("tpr.posting_date >= %(from_date)s")
    if filters.to_date:
        conditions.append("tpr.posting_date <= %(to_date)s")

    return conditions and " where " + " and ".join(conditions) or ""
