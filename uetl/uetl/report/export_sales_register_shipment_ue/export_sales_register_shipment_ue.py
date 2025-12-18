# Copyright (c) 2025, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from uetl.uetl.report import csv_to_columns
from erpnext import get_default_currency


def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_data(filters):

    conditions = ""
    data = frappe.db.sql("""
			select 
				tsi.name sales_invoice, 
				tsi.customer , 
				tsi.posting_date , 
				tsu.shipping_bill_no , 
				tsu.shipping_bill_date , 
				tsu.port_of_loading , 
				tsu.bl_no , dbk_value , 
				tsu.rodtep_value , 
				tsu.freight_cost , 
				tsu.insurance_cost , 
				tsu.other_charges , 
				tsu.fob_value , 
				tsu.exchange_rate 
			from `tabSales Invoice` tsi
			left outer join `tabShipment UE` tsu on tsu.sales_invoice =  tsi.name
			where tsi.posting_date between %(from_date)s and %(to_date)s {0}
			order by tsi.posting_date
        """.format(conditions), filters, as_dict=True)
    return data


def get_columns(filters):
    columns = """
    Sales Invoice,sales_invoice,Link/Sales Invoice,,180
    Customer,customer,Link/Customer,,300
	invoice Date,posting_date,Date,,120
	Shipping Bill No,shipping_bill_no,Data,,180 
	Shipping Bill Date,shipping_bill_date,Date,,130 
	Port of Loading,port_of_loading,Data,,180 
	BL No,bl_no,Data,,180
 	DBK Value,dbk_value,Currency,,130 
	RODTEP Value,rodtep_value,Currency,,130 
	Freight Cost,freight_cost,Currency,,130 
	Insurance Cost,insurance_cost,Currency,,130 
	Other Charges,other_charges,Currency,,130 
	FOB Value,fob_value,Currency,,130 
	Exchange Rate,exchange_rate,Currency,,130
 """
    columns = csv_to_columns(columns)

    return columns
