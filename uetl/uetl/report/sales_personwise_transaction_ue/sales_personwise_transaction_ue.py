# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.selling.report.sales_person_wise_transaction_summary.sales_person_wise_transaction_summary import (
    get_conditions,
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

    if filters["doc_type"] == "Sales Order":
        entries = frappe.db.sql(
            """
                SELECT
                    dt.name, dt.customer, dt.territory, dt.transaction_date as posting_date, dt_item.item_code,
                    st.sales_person, st.allocated_percentage, dt_item.warehouse,
                CASE
                        WHEN dt.status = "Closed" THEN dt_item.delivered_qty * dt_item.conversion_factor
                        ELSE dt_item.stock_qty
                END as stock_qty,
                CASE
                        WHEN dt.status = "Closed" THEN (dt_item.base_net_rate * dt_item.delivered_qty * dt_item.conversion_factor)
                        ELSE dt_item.base_net_amount
                END as base_net_amount,
                dt_item.base_net_rate ,
                CASE
                        WHEN dt.status = "Closed" THEN ((dt_item.base_net_rate * dt_item.delivered_qty * dt_item.conversion_factor) * st.allocated_percentage/100)
                        ELSE dt_item.base_net_amount * st.allocated_percentage/100
                END as contribution_amt ,
                dt.customer , dt.contact_display , dt.po_no , dt.po_date , dt_item.external_part_no_cf , 
                dt_item.item_name , dt_item.item_group , dt_item.brand , tb.unified_product_group_cf , dt.status so_status ,
                tc.industry , tc.territory , tc.customer_group , dt.delivery_status , dt.billing_status ,
                tsi.name sales_invoice , tsi.posting_date sales_invoice_date ,
                rsm.sales_person_name rsm_sales_person , bu.sales_person_name bu_sales_person ,
                dt_item.business_type_cf , dt_item.cost_center , tcc.parent_cost_center , tcc_gp.parent_cost_center g_parent_cost_center ,
                dt.account_manager_cf , dt.reporting_manager_cf , dt.customer_support_cf
            FROM                                                                                                                  
                `tabSales Order` dt
                inner join `tabSales Order Item` dt_item on dt_item.parent = dt.name
                inner join `tabSales Team` st on st.parent = dt.name and st.parenttype = 'Sales Order'    
                inner join tabCustomer tc on tc.name = dt.customer
                left outer join tabBrand tb on tb.name = dt_item.brand 
                left outer join `tabSales Invoice Item` tsii on tsii.sales_order = dt.name and tsii.so_detail = dt_item.name
                left outer join `tabSales Invoice` tsi on tsi.name = tsii.parent
                left outer join `tabSales Person` rsm on rsm.name = (select parent_sales_person from `tabSales Person` x where x.name = st.sales_person)
                left outer join `tabSales Person` bu on bu.name = (select parent_sales_person from `tabSales Person` x where x.name = rsm.name)                
                left outer join `tabCost Center` tcc on tcc.name = dt_item.cost_center  
                left outer join `tabCost Center` tcc_gp on tcc_gp.name = tcc.parent_cost_center  
            WHERE dt.docstatus = 1 %s
            order by st.sales_person, dt.name desc
            """
            % (conditions,),
            tuple(values),
            as_dict=1,
            # debug=1,
        )
    else:
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
            dt_item.base_net_rate ,
            CASE
                WHEN dt.status = "Closed" THEN ((dt_item.base_net_rate * dt_item.%s * dt_item.conversion_factor) * st.allocated_percentage/100)
                ELSE dt_item.base_net_amount * st.allocated_percentage/100
            END as contribution_amt ,
            dt.ewaybill , dt.irn , dt_item.sales_order , dt_item.so_detail , dt_item.brand ,
            dt.contact_display , dt.po_no , dt.po_date , tsoi.external_part_no_cf , dt_item.item_name , 
            tb.unified_product_group_cf , dt.status , rsm.sales_person_name rsm_sales_person , bu.sales_person_name bu_sales_person ,
            dt.customer_group , tsoi.business_type_cf , tsoi.cost_center , tcc.parent_cost_center , 
            tcc_gp.parent_cost_center g_parent_cost_center , dt_item.item_group , tc.industry , 
            DATE(tsoi.creation) so_date ,
            dt.account_manager_cf , dt.reporting_manager_cf , dt.customer_support_cf
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
            # debug=1,
        )

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


def get_columns(filters):
    if filters["doc_type"] == "Sales Order":
        columns = """[
                {'label':'Sales Order No','fieldname':'name','fieldtype':'Link','options':'Sales Order','width':'140'},
                {'label':'Posting Date','fieldname':'posting_date','fieldtype':'Date','options':'','width':'140'},
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
                {'label':'Unit Price','fieldname':'base_net_rate','fieldtype':'Currency','options':'','width':'140'},
                {'label':'Amount','fieldname':'base_net_amount','fieldtype':'Currency','options':'','width':'140'},
                {'label':'Status','fieldname':'so_status','fieldtype':'Data','options':'','width':'140'},
                {'label':'Delivery Status','fieldname':'delivery_status','fieldtype':'Data','options':'','width':'140'},
                {'label':'Billing Status','fieldname':'billing_status','fieldtype':'Data','options':'','width':'140'},
                {'label':'Invoice No','fieldname':'sales_invoice','fieldtype':'Link','options':'Sales Invoice','width':'140'},
                {'label':'Invoice Date','fieldname':'sales_invoice_date','fieldtype':'Date','options':'','width':'140'},
                {'label':'Sales Person','fieldname':'sales_person','fieldtype':'Link','options':'Sales Person','width':'140'},
                {'label':'RSM Person','fieldname':'rsm_sales_person','fieldtype':'Data','options':'','width':'140'},
                {'label':'Business Unit (Sales)','fieldname':'bu_sales_person','fieldtype':'Data','options':'','width':'140'},
                {'label':'Territory','fieldname':'territory','fieldtype':'Link','options':'Territory','width':'140'},
                {'label':'Customer Group','fieldname':'customer_group','fieldtype':'Data','options':'','width':'140'},
                {'label':'Industry','fieldname':'industry','fieldtype':'Data','options':'','width':'140'},
                {'label':'Business Type','fieldname':'business_type_cf','fieldtype':'Data','options':'','width':'140'},
                {'label':'Business Unit(Sourcing)','fieldname':'cost_center','fieldtype':'Link','options':'Cost Center','width':'140'},
                {'label':'Business Unit(TL/Product Group)','fieldname':'parent_cost_center','fieldtype':'Data','options':'Cost Center','width':'140'},
                {'label':'Business Unit(Product)','fieldname':'g_parent_cost_center','fieldtype':'Data','options':'Cost Center','width':'140'},
                {'label':'Account Manager','fieldname':'account_manager_cf','fieldtype':'Data','options':'','width':'140'},
                {'label':'Reporting Manager','fieldname':'reporting_manager_cf','fieldtype':'Data','options':'','width':'140'},
                {'label':'Customer Support','fieldname':'customer_support_cf','fieldtype':'Data','options':'','width':'140'}
                ]"""
    else:
        columns = """[
                {'label':'Sales Invoice','fieldname':'name','fieldtype':'Link','options':'Sales Invoice','width':'140'},
                {'label':'Posting Date','fieldname':'posting_date','fieldtype':'Date','options':'','width':'140'},
                {'label':'IRN No','fieldname':'irn','fieldtype':'Data','options':'','width':'140'},
                {'label':'E-Way Bill No','fieldname':'ewaybill','fieldtype':'Data','options':'','width':'140'},
                {'label':'Sales Order No','fieldname':'sales_order','fieldtype':'Link','options':'Sales Order','width':'140'},
                {'label':'Sales Order Date','fieldname':'so_date','fieldtype':'Date','width':'140'},
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
                {'label':'Unit Price','fieldname':'base_net_rate','fieldtype':'Currency','options':'','width':'140'},
                {'label':'Amount','fieldname':'base_net_amount','fieldtype':'Currency','options':'','width':'140'},
                {'label':'Status','fieldname':'status','fieldtype':'Data','options':'','width':'140'},
                {'label':'Sales Person','fieldname':'sales_person','fieldtype':'Link','options':'Sales Person','width':'140'},
                {'label':'RSM Person','fieldname':'rsm_sales_person','fieldtype':'Data','options':'','width':'140'},
                {'label':'Business Unit (Sales)','fieldname':'bu_sales_person','fieldtype':'Data','options':'','width':'140'},
                {'label':'Territory','fieldname':'territory','fieldtype':'Link','options':'Territory','width':'140'},
                {'label':'Customer Group','fieldname':'customer_group','fieldtype':'Data','options':'','width':'140'},
                {'label':'Industry','fieldname':'industry','fieldtype':'Data','options':'','width':'140'},
                {'label':'Business Type','fieldname':'business_type_cf','fieldtype':'Data','options':'','width':'140'},
                {'label':'Business Unit(Sourcing)','fieldname':'cost_center','fieldtype':'Link','options':'Cost Center','width':'140'},
                {'label':'Business Unit(TL/Product Group)','fieldname':'parent_cost_center','fieldtype':'Data','options':'Cost Center','width':'140'},
                {'label':'Business Unit(Product)','fieldname':'g_parent_cost_center','fieldtype':'Data','options':'Cost Center','width':'140'},
                {'label':'Account Manager','fieldname':'account_manager_cf','fieldtype':'Data','options':'','width':'140'},
                {'label':'Reporting Manager','fieldname':'reporting_manager_cf','fieldtype':'Data','options':'','width':'140'},
                {'label':'Customer Support','fieldname':'customer_support_cf','fieldtype':'Data','options':'','width':'140'}
                ]"""

    return json.loads(columns.replace("'", '"'))
