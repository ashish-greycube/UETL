# Copyright (c) 2025, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today
from uetl.uetl.report import csv_to_columns
from erpnext import get_default_currency
from india_compliance.gst_india.report.gst_purchase_register.gst_purchase_register import execute as _execute
from erpnext import get_company_currency, get_default_company


def execute(filters=None):
    result = _execute(filters)

    columns, data = get_columns(result[0]), get_data(filters, result[1])
    return columns, data


def get_data(filters, data):

    custom_data = frappe.db.sql("""
	select
		tpr.name ,
	    tpr.custom_inco_terms ,
		tpr.custom_igst ,
		tpr.custom_customs_duty ,
		tpr.custom_assessable_value ,
		tpr.custom_boe_date ,
		tpr.custom_boe_no
	from `tabPurchase Receipt` tpr
	where tpr.posting_date between %(from_date)s and %(to_date)s
                                """, filters, as_dict=True)

    custom_data_dict = {}

    for d in custom_data:
        custom_data_dict[d.name] = d

    for d in data:
        d.update(custom_data_dict.get(d.get("voucher_no", {})) or {})

    return data


def get_columns(columns):
    additional_columns = """
		Inco Terms,custom_inco_terms,,,200
		IGST,custom_igst,Currency,,130
		Customs Duty,custom_customs_duty,Currency,,130
		Assesable Value,custom_assessable_value,Data,,130
		BOE Date,custom_boe_date,Date,,130
		BOE No,custom_boe_no,Data,,130
		"""
    columns = columns + csv_to_columns(additional_columns)

    return columns
