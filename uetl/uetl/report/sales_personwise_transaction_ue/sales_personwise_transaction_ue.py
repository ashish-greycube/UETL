# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.selling.report.sales_person_wise_transaction_summary.sales_person_wise_transaction_summary import (
    get_conditions,
)
from erpnext import get_company_currency
from uetl.uetl.report import csv_to_columns
import json


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
                    dt.name, dt.customer, tc.territory, dt.transaction_date as posting_date, dt_item.item_code,
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
                dt_item.item_name , dt_item.item_group , ti.brand , tb.unified_product_group_cf , dt.status so_status ,
                tc.industry , tc.customer_group , dt.delivery_status , dt.billing_status ,
                -- tsi.name sales_invoice , tsi.posting_date sales_invoice_date ,
                rsm.sales_person_name rsm_sales_person , bu.sales_person_name bu_sales_person ,
                dt_item.business_type_cf , dt_item.cost_center , tcc.parent_cost_center , tcc_gp.parent_cost_center g_parent_cost_center ,
                dt.account_manager_cf , dt.reporting_manager_cf , dt.customer_support_cf ,
            -- custom columns from Customer
            tc.custom_line_of_business , 
            tc.custom_potential , 
            tc.parent_customer_name_cf ,
            tc.customer_id_cf ,
            tc.custom_customer_group_company ,
            tc.custom_tier ,
            tb.custom_parent_make ,
            tc.gst_category
            FROM                                                                                                                  
                `tabSales Order` dt
                inner join `tabSales Order Item` dt_item on dt_item.parent = dt.name
                inner join `tabItem` ti on ti.name = dt_item.item_code
                inner join `tabSales Team` st on st.parent = dt.name and st.parenttype = 'Sales Order'    
                inner join tabCustomer tc on tc.name = dt.customer
                left outer join tabBrand tb on tb.name = dt_item.brand 
                -- left outer join `tabSales Invoice Item` tsii on tsii.sales_order = dt.name and tsii.so_detail = dt_item.name
                -- left outer join `tabSales Invoice` tsi on tsi.name = tsii.parent
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
                dt.name, dt.customer, tc.territory, dt.%s as posting_date, dt_item.item_code,
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
            DATE(tsoi.creation) so_date , tsoi.delivery_date tsoi_delivery_date ,
            dt.account_manager_cf , dt.reporting_manager_cf , dt.customer_support_cf ,
            dt_item.batch_no , dt_item.batch_no , dt.payment_terms_template , dt_item.uom ,tsoi.purchaser_cf , 
            tso.delivery_date , ta.country ,
            -- custom columns from Customer
            tc.custom_line_of_business , 
            tc.custom_potential , 
            tc.parent_customer_name_cf ,
            tc.customer_id_cf ,
            tc.custom_customer_group_company ,
            tc.custom_tier ,
            tb.custom_parent_make ,
            case when nullif(dt.custom_sez_file_attachment,'') is null then 1 else 0 end is_pending_sez ,
            tc.gst_category
            FROM
                `tabSales Invoice` dt 
                inner join `tabSales Invoice Item` dt_item on dt_item.parent = dt.name 
                inner join `tabSales Team` st on st.parent = dt.name and st.parenttype = 'Sales Invoice'
                inner join tabCustomer tc on tc.name = dt.customer
                left outer join `tabSales Order Item` tsoi on tsoi.parent = dt_item.sales_order and tsoi.name = dt_item.so_detail 
                left outer join `tabSales Order` tso on tso.name = tsoi.parent
                left outer join tabBrand tb on tb.name = dt_item.brand 
                left outer join `tabSales Person` rsm on rsm.name = (select parent_sales_person from `tabSales Person` x where x.name = st.sales_person)
                left outer join `tabSales Person` bu on bu.name = (select parent_sales_person from `tabSales Person` x where x.name = rsm.name)
                left outer join `tabCost Center` tcc on tcc.name = tsoi.cost_center  
                left outer join `tabCost Center` tcc_gp on tcc_gp.name = tcc.parent_cost_center  
                left outer join tabAddress ta on ta.name = dt.customer_address
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
