# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.selling.report.sales_person_wise_transaction_summary.sales_person_wise_transaction_summary import (
    get_items
)
from erpnext import get_company_currency
from uetl.uetl.report import csv_to_columns
import json
from frappe.desk.reportview import build_match_conditions
from frappe.query_builder import Case, Criterion
from pypika.terms import LiteralValue


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    entries = get_entries(filters)
    data = entries

    if data:
        total_row = [""] * len(data[0])
        data.append(total_row)

    return columns, data


def get_columns(filters):
    if filters["doc_type"] == "Sales Order":
        return csv_to_columns(
            """
Sales Order No,name,Link,Sales Order,140
Posting Date,posting_date,Date,,140
Customer,customer,Link,Customer,140
Customer Buyer,contact_display,Data,,140
Customer Reference (CPO #),po_no,Link,Purchase Order,140
Customers Purchase Order Date,po_date,Date,,140
External Part #,external_part_no_cf,Data,,140
Item Code,item_code,Link,Item,140
Item Name,item_name,Data,,140
Item Group,item_group,Link,Item Group,140
UPG,unified_product_group_cf,Data,,140
Brand,brand,Link,Brand,140
Parent Brand,custom_parent_make,Link,Brand,140
Qty,stock_qty,Float,,140
Unit Price,base_net_rate,Currency,,140
Amount,base_net_amount,Currency,,140
Status,so_status,Data,,140
Delivery Status,delivery_status,Data,,140
Billing Status,billing_status,Data,,140
Sales Person,sales_person,Link,Sales Person,140
RSM Person,rsm_sales_person,Data,,140
Business Unit (Sales),bu_sales_person,Data,,140
Territory,territory,Link,Territory,140
Customer Group,customer_group,Data,,140
Industry,industry,Data,,140
Business Type,business_type_cf,Data,,140
Business Unit(Sourcing),cost_center,Link,Cost Center,140
Business Unit(TL/Product Group),parent_cost_center,Data,Cost Center,140
Business Unit(Product),g_parent_cost_center,Data,Cost Center,140
Account Manager,account_manager_cf,Data,,140
Reporting Manager,reporting_manager_cf,Data,,140
Customer Support,customer_support_cf,Data,,140
Line Of Business,custom_line_of_business,Data,,140
Potential,custom_potential,Data,,140
Parent Customer,parent_customer_name_cf,Data,,140
Customer ID,customer_id_cf,Data,,140
Customer Group Company,custom_customer_group_company,Data,,140
Tier,custom_tier,Data,,140
""")
    else:
        return csv_to_columns("""
Sales Invoice,name,Link,Sales Invoice,140
Posting Date,posting_date,Date,,140
IRN No,irn,Data,,140
E-Way Bill No,ewaybill,Data,,140
Sales Order No,sales_order,Link,Sales Order,140
Sales Order Date,so_date,Date,,140
Customer,customer,Link,Customer,140
Customer Buyer,contact_display,Data,,140
Customer Reference (CPO #),po_no,Link,Purchase Order,140
Customers Purchase Order Date,po_date,Date,,140
External Part #,external_part_no_cf,Data,,140
Item Code,item_code,Link,Item,140
Item Name,item_name,Data,,140
Item Group,item_group,Link,Item Group,140
UPG,unified_product_group_cf,Data,,140
Brand,brand,Link,Brand,140
Parent Brand,custom_parent_make,Link,Brand,140
Qty,stock_qty,Float,,140
Unit Price,base_net_rate,Currency,,140
Amount,base_net_amount,Currency,,140
Status,status,Data,,140
Sales Person,sales_person,Link,Sales Person,140
RSM Person,rsm_sales_person,Data,,140
Business Unit (Sales),bu_sales_person,Data,,140
Territory,territory,Link,Territory,140
Customer Group,customer_group,Data,,140
Industry,industry,Data,,140
Business Type,business_type_cf,Data,,140
Business Unit(Sourcing),cost_center,Link,Cost Center,140
Business Unit(TL/Product Group),parent_cost_center,Data,Cost Center,140
Business Unit(Product),g_parent_cost_center,Data,Cost Center,140
Account Manager,account_manager_cf,Data,,140
Reporting Manager,reporting_manager_cf,Data,,140
Customer Support,customer_support_cf,Data,,140   
Line Of Business,custom_line_of_business,Data,,140
Potential,custom_potential,Data,,140
Parent Customer,parent_customer_name_cf,Data,,140
Customer ID,customer_id_cf,Data,,140
Customer Group Company,custom_customer_group_company,Data,,140
Tier,custom_tier,Data,,140        
""")

def get_entries(filters):
	doc_type = filters["doc_type"]
	is_so = doc_type == "Sales Order"

	date_field = "transaction_date" if is_so else "posting_date"
	qty_field = "delivered_qty" if is_so else "qty"

	dt = frappe.qb.DocType(doc_type)
	dt_item = frappe.qb.DocType(f"{doc_type} Item")
	st = frappe.qb.DocType("Sales Team")
	ti = frappe.qb.DocType("Item")
	tb = frappe.qb.DocType("Brand")
	tc = frappe.qb.DocType("Customer")
	tcc = frappe.qb.DocType("Cost Center").as_("tcc")
	tcc_gp = frappe.qb.DocType("Cost Center").as_("tcc_gp")
	rsm = frappe.qb.DocType("Sales Person").as_("rsm")
	bu = frappe.qb.DocType("Sales Person").as_("bu")
	sp_lookup = frappe.qb.DocType("Sales Person")  # used only inside subqueries below

	# SI-only tables
	if not is_so:
		tsoi = frappe.qb.DocType("Sales Order Item").as_("tsoi")
		tso = frappe.qb.DocType("Sales Order").as_("tso")
		ta = frappe.qb.DocType("Address").as_("ta")

	# --- conditional/calculated columns -------------------------------------------------
	calc_qty = dt_item[qty_field] * dt_item.conversion_factor
	calc_net_amount = dt_item.base_net_rate * calc_qty

	stock_qty_case = Case().when(dt.status == "Closed", calc_qty).else_(dt_item.stock_qty).as_("stock_qty")

	base_net_amount_case = (
		Case()
		.when(dt.status == "Closed", calc_net_amount)
		.else_(dt_item.base_net_amount)
		.as_("base_net_amount")
	)

	contribution_amt_case = (
		Case()
		.when(dt.status == "Closed", (calc_net_amount * st.allocated_percentage / 100))
		.else_(dt_item.base_net_amount * st.allocated_percentage / 100)
		.as_("contribution_amt")
	)

	status_alias = "so_status" if is_so else "status"

	doc_filters = {"docstatus": 1}
	for field in ["company", "customer", "territory"]:
		if filters.get(field):
			doc_filters[field] = filters.get(field)

	if filters.get("from_date") and filters.get("to_date"):
		doc_filters[date_field] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	elif filters.get("from_date"):
		doc_filters[date_field] = [">=", filters.get("from_date")]
	elif filters.get("to_date"):
		doc_filters[date_field] = ["<=", filters.get("to_date")]

	rsm_parent_sq = (
		frappe.qb.from_(sp_lookup)
		.select(sp_lookup.parent_sales_person)
		.where(sp_lookup.name == st.sales_person)
	)
	bu_parent_sq = (
		frappe.qb.from_(sp_lookup)
		.select(sp_lookup.parent_sales_person)
		.where(sp_lookup.name == rsm.name)
	)

	query = (
		frappe.get_query(dt, filters=doc_filters)
		.join(dt_item)
		.on(dt.name == dt_item.parent)
		.join(st)
		.on(dt.name == st.parent)
		.join(ti)
		.on(ti.name == dt_item.item_code)
		.join(tc)
		.on(tc.name == dt.customer)
		.left_join(tb)
		.on(tb.name == ti.brand)
		.left_join(rsm)
		.on(rsm.name == rsm_parent_sq)
		.left_join(bu)
		.on(bu.name == bu_parent_sq)
		.where(st.parenttype == doc_type)
	)

	# cost-center source differs: SO uses dt_item directly, SI uses tsoi
	if is_so:
		query = (
			query.left_join(tcc)
			.on(tcc.name == dt_item.cost_center)
			.left_join(tcc_gp)
			.on(tcc_gp.name == tcc.parent_cost_center)
		)
	else:
		query = (
			query.left_join(tsoi)
			.on((tsoi.parent == dt_item.sales_order) & (tsoi.name == dt_item.so_detail))
			.left_join(tso)
			.on(tso.name == tsoi.parent)
			.left_join(ta)
			.on(ta.name == dt.customer_address)
			.left_join(tcc)
			.on(tcc.name == tsoi.cost_center)
			.left_join(tcc_gp)
			.on(tcc_gp.name == tcc.parent_cost_center)
		)

	query = query.select(
		dt.name,
		dt.customer,
		tc.territory,  
		dt[date_field].as_("posting_date"),
		dt_item.item_code,
		st.sales_person,
		st.allocated_percentage,
		dt_item.warehouse,
		stock_qty_case,
		base_net_amount_case,
		dt_item.base_net_rate,
		contribution_amt_case,
		dt.contact_display,
		dt.po_no,
		dt.po_date,
		dt_item.item_name,
		ti.brand,
		tb.unified_product_group_cf,
		tb.custom_parent_make,
		dt.status.as_(status_alias),
		rsm.sales_person_name.as_("rsm_sales_person"),
		bu.sales_person_name.as_("bu_sales_person"),
		tcc.parent_cost_center,
		tcc_gp.parent_cost_center.as_("g_parent_cost_center"),
		dt.account_manager_cf,
		dt.reporting_manager_cf,
		dt.customer_support_cf,
		tc.industry,
		tc.customer_group,
		tc.custom_line_of_business,
		tc.custom_potential,
		tc.parent_customer_name_cf,
		tc.customer_id_cf,
		tc.custom_customer_group_company,
		tc.custom_tier,
		tc.gst_category,
	)

	if is_so:
		query = query.select(
			dt_item.external_part_no_cf,
			dt_item.item_group,
			dt.delivery_status,
			dt.billing_status,
			dt_item.business_type_cf,
			dt_item.cost_center,
		)
	else:
		is_pending_sez_case = (
			Case()
			.when(LiteralValue("nullif(custom_sez_file_attachment,'') is null"), 1)
			.else_(0)
			.as_("is_pending_sez")
		)
		query = query.select(
			dt.ewaybill,
			dt.irn,
			dt_item.sales_order,
			dt_item.so_detail,
			tsoi.external_part_no_cf,
			dt_item.item_group,
			tsoi.creation.as_("so_date"),
			tsoi.delivery_date.as_("tsoi_delivery_date"),
			dt_item.batch_no,
			dt.payment_terms_template,
			dt_item.uom,
			tsoi.purchaser_cf,
			tso.delivery_date,
			ta.country,
			is_pending_sez_case,
			tsoi.business_type_cf,
			tsoi.cost_center,
		)

	if filters.get("sales_person"):
		lft, rgt = frappe.db.get_value("Sales Person", filters.get("sales_person"), ["lft", "rgt"])
		sp = frappe.qb.DocType("Sales Person")
		query = query.where(
			st.sales_person.isin(frappe.qb.from_(sp).select(sp.name).where((sp.lft >= lft) & (sp.rgt <= rgt)))
		)

	# only resolve items when an item_group/brand filter is set; otherwise get_items
	# would return every item in the system and add a huge IN() clause on each run
	if filters.get("item_group") or filters.get("brand"):
		items = get_items(filters)
		if not items:
			return []
		query = query.where(dt_item.item_code.isin([d[0] for d in items]))

	query = query.orderby(st.sales_person).orderby(dt.name, order=frappe.qb.desc)

	match_conditions = build_match_conditions(doc_type)
	if match_conditions:
		query = query.where(LiteralValue(match_conditions))

	entries = query.run(as_dict=True)

	if filters.get("cost_center"):
		cc = filters.get("cost_center")
		entries = [
			d
			for d in entries
			if cc == d.cost_center
			or cc == d.parent_cost_center
			or cc == d.g_parent_cost_center
		]

	return entries