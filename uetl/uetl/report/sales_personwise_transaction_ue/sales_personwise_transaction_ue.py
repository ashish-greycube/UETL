# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.selling.report.sales_person_wise_transaction_summary.sales_person_wise_transaction_summary import (
    get_conditions,
    get_item_details,
)
from erpnext import get_company_currency
import json


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    entries = get_entries(filters)
    data = entries

    company_currency = get_company_currency(filters.get("company"))

    if data:
        total_row = [""] * len(data[0])
        data.append(total_row)

    return columns, data


def get_entries(filters):
    date_field = (
        filters["doc_type"] == "Sales Order" and "transaction_date" or "posting_date"
    )
    if filters["doc_type"] == "Sales Order":
        qty_field = "delivered_qty"
    else:
        qty_field = "qty"
    conditions, values = get_conditions(filters, date_field)

    if filters.get("show_return_entries", 0):
        conditions = (
            conditions
            + " and (dt_item.stock_qty > 0 or (dt.status = 'Closed' and dt_item.{} > 0))".format(
                qty_field
            )
        )

    entries = frappe.db.sql(
        """
		SELECT
			dt.name, dt.customer, dt.territory, dt.%s as posting_date, dt_item.item_code,
			st.sales_person, st.allocated_percentage, dt_item.warehouse,
		CASE
			WHEN dt.status = "Closed" THEN dt_item.%s * dt_item.conversion_factor
			ELSE dt_item.stock_qty
		END as stock_qty,
		CASE
			WHEN dt.status = "Closed" THEN (dt_item.base_net_rate * dt_item.%s * dt_item.conversion_factor)
			ELSE dt_item.base_net_amount
		END as base_net_amount,
		CASE
			WHEN dt.status = "Closed" THEN ((dt_item.base_net_rate * dt_item.%s * dt_item.conversion_factor) * st.allocated_percentage/100)
			ELSE dt_item.base_net_amount * st.allocated_percentage/100
		END as contribution_amt ,
		dt.ewaybill , dt.irn , dt_item.sales_order , dt_item.so_detail , dt_item.brand ,
		dt.contact_display , dt.po_no , dt.po_date , tsoi.external_part_no_cf , dt_item.item_name , 
        tb.unified_product_group_cf , dt.status , rsm.sales_person_name rsm_sales_person , bu.sales_person_name bu_sales_person ,
		dt.customer_group , tsoi.business_type_cf , tsoi.cost_center , tcc.parent_cost_center , 
        tcc_gp.parent_cost_center g_parent_cost_center , dt_item.item_group , tc.industry
		FROM
			`tabSales Invoice` dt 
			inner join `tabSales Invoice Item` dt_item on dt_item.parent = dt.name 
			inner join `tabSales Team` st on st.parent = dt.name and st.parenttype = 'Sales Invoice'
            inner join tabCustomer tc on tc.name = dt.customer
			left outer join `tabSales Order Item` tsoi on tsoi.parent = dt_item.sales_order and tsoi.name = dt_item.so_detail 
			left outer join tabBrand tb on tb.name = dt_item.brand 
			left outer join `tabSales Person` rsm on rsm.name = (select parent_sales_person from `tabSales Person` x where x.name = st.sales_person)
			left outer join `tabSales Person` bu on bu.name = (select parent_sales_person from `tabSales Person` x where x.name = rsm.name)
			left outer join `tabCost Center` tcc on tcc.name = tsoi.cost_center  
			left outer join `tabCost Center` tcc_gp on tcc_gp.name = tcc.parent_cost_center  
		WHERE
            dt.docstatus = 1 %s order by st.sales_person, dt.name desc
		"""
        % (
            date_field,
            qty_field,
            qty_field,
            qty_field,
            conditions,
        ),
        tuple(values),
        as_dict=1,
        debug=1,
    )

    return entries


def get_columns(filters):
    columns = """[
            {'label':'Sales Invoice','fieldname':'name','fieldtype':'Link','options':'Sales Invoice','width':'140'},
            {'label':'Posting Date','fieldname':'posting_date','fieldtype':'Date','options':'','width':'140'},
            {'label':'IRN No','fieldname':'irn','fieldtype':'Data','options':'','width':'140'},
            {'label':'E-Way Bill No','fieldname':'ewaybill','fieldtype':'Data','options':'','width':'140'},
            {'label':'Sales Order No','fieldname':'sales_order','fieldtype':'Link','options':'Sales Order','width':'140'},
            {'label':'Customer','fieldname':'customer','fieldtype':'Link','options':'Customer','width':'140'},
            {'label':'Customer Buyer','fieldname':'contact_display','fieldtype':'Data','options':'','width':'140'},
            {'label':'Customer Reference (CPO #)','fieldname':'po_no','fieldtype':'Link','options':'Purchase Order','width':'140'},
            {'label':'Customers Purchase Order Date','fieldname':'po_date','fieldtype':'Date','options':'','width':'140'},
            {'label':'External Part #','fieldname':'external_part_no_cf','fieldtype':'Data','options':'','width':'140'},
            {'label':'Item Code','fieldname':'item_code','fieldtype':'Link','options':'Item','width':'140'},
            {'label':'Item Name','fieldname':'item_name','fieldtype':'Data','options':'','width':'140'},
            {'label':'Item Group','fieldname':'item_group','fieldtype':'Link','options':'Item Group','width':'140'},
            {'label':'UPG','fieldname':'unified_product_group_cf','fieldtype':'Data','options':'','width':'140'},
            {'label':'Brand','fieldname':'brand','fieldtype':'Link','options':'Brand','width':'140'},
            {'label':'Qty','fieldname':'stock_qty','fieldtype':'Float','options':'','width':'140'},
            {'label':'Amount','fieldname':'base_net_amount','fieldtype':'Currency','options':'','width':'140'},
            {'label':'Status','fieldname':'status','fieldtype':'Data','options':'','width':'140'},
            {'label':'Sales Person','fieldname':'sales_person','fieldtype':'Link','options':'Sales Person','width':'140'},
            {'label':'Sales Person - P','fieldname':'rsm_sales_person','fieldtype':'Data','options':'','width':'140'},
            {'label':'Sales Person - GP','fieldname':'bu_sales_person','fieldtype':'Data','options':'','width':'140'},
            {'label':'Territory','fieldname':'territory','fieldtype':'Link','options':'Territory','width':'140'},
            {'label':'Customer Group','fieldname':'customer_group','fieldtype':'Data','options':'','width':'140'},
            {'label':'Industry','fieldname':'industry','fieldtype':'Data','options':'','width':'140'},
            {'label':'Business Type','fieldname':'business_type_cf','fieldtype':'Data','options':'','width':'140'},
            {'label':'Cost Center (SO Item)','fieldname':'cost_center','fieldtype':'Link','options':'Cost Center','width':'140'},
            {'label':'Cost Center-P - (SO Item)','fieldname':'parent_cost_center','fieldtype':'Link','options':'Cost Center','width':'140'},
            {'label':'Cost Center-GP - (SO Item)','fieldname':'g_parent_cost_center','fieldtype':'Link','options':'Cost Center','width':'140'}
            ]"""

    return json.loads(columns.replace("'", '"'))