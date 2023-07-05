# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today
from erpnext import get_default_currency

from uetl.uetl.report import csv_to_columns


def execute(filters=None):
    filters["today"] = today()

    columns, data = get_columns(), get_data(filters)
    return columns, data


def get_columns():
    columns = """
    Customer,customer,Link/Customer,,140
    Item Code,item_code,Link/Item,,200
    Item Name,item_name,,,200
    Item Group,item_group,,,130
    Batch,batch_id,,,110
    Supplier,supplier,,,120
    Purchase Receipt,reference_name,Link/Purchase Receipt,,130
    Purchase Receipt Date,pr_date,Date,,130
    Received Qty,received_qty,Float,,130
    Sold Qty,sold_qty,Float,,130
    Sold Date,dn_date,Date,,120
    Balance Quantity,balance_qty,Float,,130
    Age (in Days),age_in_days,Int,,130
    Rate,base_rate,Currency,,130
    Amount({}),amount,Currency,,130
    Cost Center,cost_center,,,130
    Purchaser,purchaser_cf,,,120
    Sales Person,sales_person,,,150
    BU Product Team,grand_parent_cost_center,,<150
    BU Product,parent_cost_center,,,150
    RSM Team,parent_cost_center,,,150
    BU Sales,grand_parent_cost_center,,,150
    """.format(
        get_default_currency()
    )
    return csv_to_columns(columns)


def get_data(filters):
    data = frappe.db.sql(
        """
select * , 
	case when t.balance_qty > 0 then DATEDIFF(%(today)s, t.pr_date)
		else datediff(t.pr_date,t.dn_date) end age_in_days
from
(
	select 
        ti.item_code , ti.item_name , ti.item_group , 
        tb.batch_id , tb.supplier , tb.reference_doctype , tb.reference_name ,
        tpr.posting_date pr_date , tpri.received_qty , tdni.qty sold_qty , tdn.posting_date dn_date , 
        tpri.received_qty - tdni.qty  balance_qty ,
        tpri.base_rate , tpri.received_qty * tpri.base_rate amount ,
        tsoi.purchaser_cf , tso.customer ,
        tst.sales_person , tsp.parent_sales_person , tsgp.parent_sales_person grand_parent_sales_person ,
        tsoi.cost_center , tccp.parent_cost_center , tccgp.parent_cost_center grand_parent_cost_center 
    from tabBatch tb 
    inner join tabItem ti on ti.name = tb.item 
    left outer join `tabPurchase Receipt` tpr on tpr.name = tb.reference_name 
    left outer join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name
    left outer join `tabSales Order Item` tsoi on tsoi.name = tpri.sales_order_item_cf
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
    left outer join `tabDelivery Note` tdn on tdn.name = tdni.parent {}
) t    
    """.format(
            get_conditions(filters)
        ),
        filters,
        as_dict=True,
    )

    if filters.inventory_type == "Sold":
        data = [d for d in data if d.balance_qty == 0]
    if filters.inventory_type == "Pending":
        data = [d for d in data if not d.balance_qty == 0]
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

    return conditions and " where " + " and ".join(conditions) or ""
