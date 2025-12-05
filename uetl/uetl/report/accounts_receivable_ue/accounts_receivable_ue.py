# Copyright (c) 2025, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today
from uetl.uetl.report import csv_to_columns
from erpnext import get_default_currency
from erpnext.accounts.report.accounts_receivable.accounts_receivable import execute as ar_execute


def execute(filters=None):
    result = ar_execute(filters)

    columns, data = get_columns(result[0]), get_data(filters, result[1])
    return columns, data


def get_data(filters, data):

    custom_data = frappe.db.sql("""
			select 
				tst.parent sales_invoice, tst.sales_person , rsm.name rsm, bu.name bu, 
    			tc.parent_customer_name_cf parent_customer, tsi.payment_terms_template 
			from `tabSales Team` tst
			inner join `tabSales Invoice` tsi on tsi.name = tst.parent 
			left outer join `tabSales Person` rsm on rsm.name = 
				(select parent_sales_person from `tabSales Person` x where x.name = tst.sales_person)
			left outer join `tabSales Person` bu on bu.name = 
				(select parent_sales_person from `tabSales Person` x where x.name = rsm.name) 
			left outer join tabCustomer tc on tc.name = tsi.customer
			where tst.parenttype = 'Sales Invoice'
				and tsi.posting_date <= %(report_date)s
                                """, filters, as_dict=True)

    custom_data_dict = {}

    for d in custom_data:
        custom_data_dict[d.sales_invoice] = d

    for d in data:
        if d.get("voucher_type") == "Sales Invoice":
            d.update(custom_data_dict.get(d.get("voucher_no", {})) or {})

    return data


def get_columns(columns):
    additional_columns = """
    Sales Person,sales_person,Link/Sales Person,,130
    RSM Person,rsm,Link/Sales Person,,130
    Business Unit (Sales),bu,Link/Sales Person,,130
    Parent Customer,parent_customer,Link/Customer,,140
    Payment Terms,payment_terms_template,Data,,180"""
    columns = columns + csv_to_columns(additional_columns)

    return columns
