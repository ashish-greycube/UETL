# Copyright (c) 2025, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today
from uetl.uetl.report import csv_to_columns
from erpnext import get_default_currency
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import execute as ar_summary_execute
from erpnext import get_company_currency, get_default_company


def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_data(filters):

    data = frappe.db.sql("""
	select
  			tc.name as customer,
			tc.customer_id_cf ,
			tccl.credit_limit credit_limit ,
   			0 total_outstanding ,
			0 total_amount_due ,
			t2.batch_amount total_inventory ,
			t1.open_orders ,
			t1.open_orders_booked
  		from `tabCustomer` tc
    left outer join `tabCustomer Credit Limit` tccl on tccl.parent = tc.name
		and tccl.parenttype = 'Customer' and tccl.company = %s
    left outer join (
		select
			tso.customer ,
			sum(tsoi.base_net_rate * (tsoi.stock_qty - tsoi.delivered_qty)) open_orders ,
			sum(tsoi.base_net_rate * (tsoi.ordered_qty - coalesce(tpoi.received_qty,0))) open_orders_booked
		from `tabSales Order Item` tsoi
		inner join `tabSales Order` tso on tso.name = tsoi.parent and tsoi.parenttype = 'Sales Order'
		inner join `tabPurchase Order Item` tpoi on tpoi.sales_order = tso.name
			and tpoi.item_code = tsoi.item_code
		group by tso.customer
	) t1 on t1.customer = tc.name
	left outer join (
		select 
			tso.customer ,	sum(tb.batch_qty * tpri.base_rate) batch_amount 
		from tabBatch tb
		left outer join `tabPurchase Receipt` tpr on tpr.name = tb.reference_name 
			and tpr.docstatus = 1
		left outer join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name
			and tpri.item_code = tb.item and tpri.batch_no = tb.name  
		left outer join `tabSales Order` tso on tso.name = tpri.sales_order_cf   
		group by tso.customer		
	) t2 on t2.customer = tc.name
        """, (get_default_company()),
        as_dict=True)

    ar_summary = get_accounts_receivable_summary(filters)

    for d in data:
        summary = ar_summary.get(d.customer)
        d["total_outstanding"] = summary and summary.outstanding or 0
        d["total_amount_due"] = summary and summary.total_due or 0

    return data


def get_columns(filters):
    columns = """
    Customer,customer,Link/Customer,,300
    Customer ID,customer_id_cf,,,150
    Credit Limit Set,credit_limit,Currency,,150
    Total Outstanding,total_outstanding,Currency,,150
    Payment Dues,total_amount_due,Currency,,150
    Total Inventory,total_inventory,Currency,,150
    Open Orders,open_orders,Currency,,150
    Booked Orders,open_orders_booked,Currency,,150
    """
    columns = csv_to_columns(columns)

    return columns


def get_accounts_receivable_summary(filters):

    filters = {
        "company": get_default_company(),
        "report_date": today(),
        "ageing_based_on": "Due Date",
        "calculate_ageing_with": "Report Date",
        "range": "30, 60, 90, 120",
        "cost_center": [],
        # "party": []
    }
    if not filters.get('posting_date'):
        filters['posting_date'] = today()
    result = ar_summary_execute(filters)[1]

    ar_outstanding = {}

    for d in result:
        ar_outstanding[d.party] = d

    return ar_outstanding
