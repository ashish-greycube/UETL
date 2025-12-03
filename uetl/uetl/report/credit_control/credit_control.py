# Copyright (c) 2025, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from uetl.uetl.report import csv_to_columns
from erpnext import get_default_currency
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import execute as ar_summary_execute


def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_data(filters):

    data = frappe.db.sql("""
		select 
  			tc.name as customer,
			tc.customer_id_cf ,
			0 credit_limit ,
   			0 total_outstanding ,
			0 payment_dues ,
			0 total_inventory ,
			orders.open_order_count ,
   			reserved_orders.reserved_qty ,
			0 booked_order_count
  		from `tabCustomer` tc
    left outer join (
		select 
			tso.customer, tso.customer_name, count(tso.name) open_order_count
		from `tabSales Order` tso 
		where 
			tso.docstatus = 1 
			and tso.status in ('To Deliver','To Deliver and Bill', 'To Bill', 'On Hold')		
	) orders on orders.customer = tc.name
	left outer join(
			select tso.customer , sum(tsoi.ordered_qty-coalesce(tpoi.received_qty ,0)) reserved_qty
			from `tabSales Order` tso 
			inner join `tabSales Order Item` tsoi on tsoi.parent = tso.name
				and tsoi.parenttype = 'Sales Order'
			left outer join `tabPurchase Order Item` tpoi on tpoi.sales_order_item = tsoi.name
				and tpoi.item_code = tsoi.item_code
			group by tso.customer
	) reserved_orders on reserved_orders.customer = tc.name
        """,
                         as_dict=True)

    ar_summary = get_accounts_receivable_summary(filters)

    ar_outstanding = {}

    for d in ar_summary:
        ar_outstanding[d.party] = d.outstanding

    print(ar_outstanding)

    for d in data:
        d["total_outstanding"] = ar_outstanding.get(d.customer, 0) or 0

    return data


def get_columns(filters):
    columns = """
    Customer,customer,Link/Customer,,300
    Customer ID,customer_id_cf,,,150
    Credit Limit Set,credit_limit,Currency,,150
    Total Outstanding,total_outstanding,Currency,,150
    Payment Dues,payment_dues,Currency,,150
    Total Inventory,total_inventory,Int,,150
    Open Orders,open_order_count,Int,,150
    Booked Orders,booked_order_count,Int,,150
    """
    columns = csv_to_columns(columns)

    return columns


def get_accounts_receivable_summary(filters):
    return ar_summary_execute(filters)[1]
