# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today
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
    data = frappe.db.sql(
        """
select * , 
	case 
        when t.batch_qty = 0 then DATEDIFF(t.dn_date, t.pr_date)
        when t.sold_qty > 0 then datediff(t.dn_date,t.pr_date) 
        else datediff(%(today)s,t.pr_date) end age_in_days ,
    case when t.batch_qty > 0
        then datediff(%(today)s,t.pr_date) 
        else null end batch_balance_age
from
(  
    select
        ti.item_code , ti.item_name , ti.item_group , ti.brand ,
        tb.batch_id , tb.supplier , tb.reference_doctype , tb.reference_name , tb.batch_qty ,
        tpr.posting_date pr_date , tpri.received_stock_qty , tdn.posting_date dn_date , 
        tpri.base_rate , tb.batch_qty * tpri.base_rate batch_amount ,
        tdni.stock_qty sold_qty , tdni.base_rate sold_rate , tdni.stock_qty * tdni.base_rate sold_amount ,
        tsoi.purchaser_cf , tso.customer ,
        tst.sales_person , tsp.parent_sales_person , tsgp.parent_sales_person grand_parent_sales_person ,
        tsoi.cost_center , tccp.parent_cost_center , tccgp.parent_cost_center grand_parent_cost_center 
    from tabBatch tb 
    inner join tabItem ti on ti.name = tb.item 
    left outer join `tabPurchase Receipt` tpr on tpr.name = tb.reference_name 
        and tpr.docstatus = 1
    left outer join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name
        and tpri.item_code = tb.item and tpri.batch_no = tb.name 
    left outer join `tabSales Order Item` tsoi on tsoi.name = tpri.sales_order_item_cf
        and tsoi.item_code = tpri.item_code and tsoi.docstatus = 1
    left outer join `tabSales Order` tso on tso.name = tpri.sales_order_cf 
    left outer join (
        select parent, sales_person  from `tabSales Team` tst 
        where parenttype = 'Sales Order'
        group by parent
    ) tst on tst.parent = tsoi.parent
    left outer join `tabSales Person` tsp on tsp.name = tst.sales_person 
    left outer join `tabSales Person` tsgp on tsgp.name = tsp.parent_sales_person  
    left outer JOIN `tabCost Center` tccp on tccp.name = tsoi.cost_center 
    left outer JOIN `tabCost Center` tccgp on tccgp.name = tccp.parent_cost_center 
    left outer join `tabDelivery Note Item` tdni on tdni.against_sales_order = tso.name 
        and tdni.so_detail = tsoi.name and tdni.batch_no = tb.name and tdni.item_code = tb.item
        and tdni.docstatus = 1
    left outer join `tabDelivery Note` tdn on tdn.name = tdni.parent {}
) t    
    """.format(
            get_conditions(filters)
        ),
        filters,
        as_dict=True,
    )

    if filters.customer:
        data = [d for d in data if d.customer == filters.customer]
    if filters.cost_center:
        data = [d for d in data if d.cost_center == filters.cost_center]
    if filters.sales_person:
        data = [d for d in data if d.sales_person == filters.sales_person]

    return data


def get_conditions(filters):
    conditions = []

    if filters.from_date:
        conditions.append("tpr.posting_date >= %(from_date)s")
    if filters.to_date:
        conditions.append("tpr.posting_date <= %(to_date)s")

    if filters.inventory_type == "Sold":
        conditions.append("coalesce(tdni.stock_qty,0) > 0 and tb.batch_qty = 0")
    if filters.inventory_type == "Pending":
        conditions.append("tb.batch_qty <> 0")

    return conditions and " where " + " and ".join(conditions) or ""
