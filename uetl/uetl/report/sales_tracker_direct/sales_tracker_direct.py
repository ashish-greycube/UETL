# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from itertools import groupby
from frappe.utils import cstr, cint


def execute(filters=None):
    columns, data = [], []
    return get_columns(filters), get_data(filters)


def get_data(filters=None):

    data = frappe.db.sql(
        """
select 
        	tc.name customer,
            tso.customer_name , 
            tso.po_no cpo_no, 
			DATE_FORMAT(tso.po_date,'%d/%m/%Y')  customer_po_date, 
            DATE_FORMAT(tso.creation,'%d/%m/%Y %H:%i') so_creation,
            tso.status so_status , tso.payment_terms_template ,
            tsoi.cpo_line_no_cf as cpo_line_no_cf,
            tsoi.external_part_no_cf as external_part_no_cf,
            tsoi.item_name item_number, tsoi.item_code , tsoi.item_group ,
            tsoi.brand mfr, 
            tsoi.stock_qty cpo_qty,
            tsoi.stock_qty - tsoi.ordered_qty on_order_np_qty ,
            tsoi.ordered_qty - coalesce(tpoi.received_qty,0) reserved_order_qty ,
            tsoi.ordered_qty - tsoi.delivered_qty - (coalesce(tpoi.stock_qty,0) - coalesce(tpoi.received_qty,0)) reserved_physical_qty ,
            tsoi.delivered_qty sold_qty ,
            tsoi.stock_qty - tsoi.delivered_qty pending_qty ,
            tsoi.stock_uom, 
            tsoi.base_net_rate unit_price, 
            tsoi.base_net_amount net_amount ,
            tsoi.base_net_rate * (tsoi.stock_qty - tsoi.ordered_qty) on_order_np_amount,
            tsoi.base_net_rate * (tsoi.ordered_qty - coalesce(tpoi.received_qty,0)) reserved_order_amount,
            tsoi.base_net_rate * (tsoi.ordered_qty - tsoi.delivered_qty 
                - (coalesce(tpoi.stock_qty,0) - coalesce(tpoi.received_qty,0))) reserved_physical_amount,
            tsoi.base_net_rate * (tsoi.delivered_qty) sold_amount, 
            tsoi.base_net_rate * (tsoi.stock_qty - tsoi.delivered_qty) pending_amount, 
            tso.currency , 
            DATE_FORMAT(tsoi.delivery_date,'%d-%b-%Y') requested_ship_date, 
            DATE_FORMAT(tpoi.expected_delivery_date,'%d-%b-%Y') confirmed_ship_date ,
            tsoi.special_remarks_cf as special_remarks,
            tpoi.cost_center  as sourcing,
            tsoi.purchaser_cf as purchaser,
            tsii.parent as invoice_no,
            DATE_FORMAT(tsii.posting_date, '%d-%b-%Y') as invoice_date,
            tsii.stock_qty as si_qty,
            tsii.transporter as transporter_agency,
            tsii.lr_no as awb_no,
            COALESCE (tb.manufacturing_date , DATE(tb.creation))  as material_receipt_date ,
            tpri.batch_no pr_item_batch_no, 
            tsii.batch_no si_item_batch_no,
            CASE tb.batch_qty WHEN 0 THEN 0 ELSE DATEDIFF(NOW(),COALESCE (tb.manufacturing_date , DATE(tb.creation))) END as stock_days_for_stock_qty,
            DATEDIFF(tsii.posting_date,COALESCE (tb.manufacturing_date , DATE(tb.creation))) stock_days_for_sold_qty,
            tso.name sales_order ,
            tso.contact_display customer_buyer ,
            tsoi.business_type_cf business_type ,
            tpoi.purchaser_comment_cf ,
            tsoi.cost_center tsoi_cost_center,
            tst.sales_person sales_tracked_to ,
            tc.customer_group customer_group ,
            tc.industry industry,
            tso.territory territory ,
            tccp.parent_cost_center , tccgp.parent_cost_center grand_parent_cost_center ,  
            tsp.parent_sales_person , tspp.parent_sales_person grand_parent_sales_person , 
            tbr.unified_product_group_cf ,
            case when tsoi.delivered_qty = 0 then 'Not Delivered'
                when tsoi.qty = tsoi.delivered_qty then 'Fully Delivered'
                when tsoi.qty > tsoi.delivered_qty then 'Partly Delivered'
                else '' end delivery_status ,
            case when billed_amt = 0 then 'Not Billed'
                when billed_amt < base_net_amount then 'Partly Billed'
                when billed_amt = base_net_amount then 'Fully Billed'
                else '' end billed_status ,
            tpoi.parent purchase_order, tpri.parent purchase_receipt ,
            tsii.irn , tsii.ewaybill 
            -- '~',
            -- tsoi.parent 'so', tsoi.name 'soi name', 
            -- tpoi.name 'tpoi name', tpri.name 'tpri name', tsii.name 'tsii name',
            -- tsoi.stock_qty 'soi stock_qty' , 
            -- tsoi.ordered_qty 'tsoi ordered_qty' , 
            -- tsoi.delivered_qty 'tsoi delivered_qty', 
            -- tpoi.stock_qty 'tpoi stock_qty',
            -- tpoi.received_qty 'tpoi received_qty', 
            -- tso.creation so_creation,
            -- tpoi.parent 'po', tpoi.name 'poi name',
            -- tsii.parent 'si', tsii.name 'sii name',
            -- COALESCE (tb.manufacturing_date , DATE(tb.creation)) 'tpr_posting_date', tpri.batch_no 'tpri_batch_no', tpri.item_code 'tpri_item_code',
            -- tsii.posting_date 'tsi_posting_date', tsii.batch_no 'tsii_batch_no', tsii.item_code 'tsii_item_code'
        from 
            `tabSales Order` tso
        inner join `tabSales Order Item` tsoi on tsoi.parent = tso.name 
        inner join tabItem ti on ti.name = tsoi.item_code and ti.is_stock_item = 1
		left outer join tabBrand tbr on tbr.name = ti.brand 
        left outer join (
            select 
                tpri.parent, tpri.name, tpr.posting_date, tpri.sales_order_item_cf, tpri.sales_order_cf ,
                tpri.purchase_order, tpri.purchase_order_item, tpri.batch_no, tpri.item_code
            from  `tabPurchase Receipt` tpr 
            inner join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name
            where tpr.docstatus = 1
        ) tpri on tpri.sales_order_cf = tso.name 
            and tpri.sales_order_item_cf = tsoi.name         
        left outer join (
            select 
                tsii.parent, tsii.name, tsi.posting_date, tsi.transporter, tsi.irn , tsi.ewaybill ,
                tsii.sales_order, tsii.so_detail, tsii.batch_no, tsii.item_code, tsii.stock_qty, tsi.lr_no
            from  `tabSales Invoice` tsi 
            inner join  `tabSales Invoice Item` tsii on tsii.parent = tsi.name
            where tsi.docstatus = 1
        ) tsii on tsii.sales_order = tsoi.parent 
            and tsii.so_detail = tsoi.name and tsii.sales_order = tso.name 
        left outer join (
            select 
                tpoi.parent, tpoi.name, 
                tpo.owner, tpoi.sales_order, tpoi.sales_order_item, tpoi.received_qty, 
                tpoi.stock_qty, tpoi.expected_delivery_date, tpoi.cost_center, tpoi.purchaser_comment_cf
                from  `tabPurchase Order` tpo
                inner join `tabPurchase Order Item` tpoi on tpoi.parent = tpo.name
                where tpo.docstatus = 1
        ) tpoi on tpoi.sales_order = tsoi.parent 
            and tpoi.sales_order_item = tsoi.name             
        left outer join `tabBatch` tb  on tpri.batch_no  = tb.name
        left outer join tabCustomer tc on tc.name = tso.customer
        left outer join (
            select parent, sales_person  from `tabSales Team` tst 
            group by parent
        ) tst on tst.parent = tso.name
        left outer JOIN `tabCost Center` tccp on tccp.name = tsoi.cost_center 
        left outer JOIN `tabCost Center` tccgp on tccgp.name = tccp.parent_cost_center 
        left outer join `tabSales Person` tsp on tsp.name = tst.sales_person
        left outer join `tabSales Person` tspp on tspp.name = tsp.parent_sales_person
        WHERE 
            tso.docstatus = 1 {conditions}
        order by 
            tso.name, tsoi.idx, tpri.item_code, tsii.item_code , tpri.batch_no , tsii.batch_no  
        """.format(
            conditions=get_conditions(filters)
        ),
        as_dict=True,
        debug=True,
    )

    if not data:
        return []

    if not cint(filters.get("hide_group_fields")):
        return data

    show_in_group_fields = [
        "confirmed_ship_date",
        "sourcing",
        "purchaser",
        "invoice_no",
        "invoice_date",
        "si_qty",
        "transporter_agency",
        "awb_no",
        "material_receipt_date",
        "pr_item_batch_no",
        "si_item_batch_no",
        "stock_days_for_stock_qty",
        "stock_days_for_sold_qty",
    ]

    out = []
    for key, group in groupby(data, lambda x: x["sales_order"]):
        items = list(group)
        out.append(items[0])
        for d in items[1:]:
            out.append({x: d[x] for x in d if x in show_in_group_fields})

    return out


def get_columns(filters):
    return csv_to_columns(
        """Customers Name,customer_name,,,150
Customer Buyer,customer_buyer,,,150
Customer Reference (CPO #),cpo_no,,,150
Cust PO Dt,customer_po_date,Date,,150
SO Created On,so_creation,Date,,150
CPO Line #,cpo_line_no_cf,,,150
External Part #,external_part_no_cf,,,150
Item Code,item_code,Link,Item,150
Item #,item_number,,,150
Item Group,item_group,Link,Item Group,150
UPG,unified_product_group_cf,,,150
MFR,mfr,Data,,150
CPO Qty,cpo_qty,Float,,150
On Order (NP)QTY,on_order_np_qty,Float,,150
Reserved Order Qty,reserved_order_qty,Float,,150
Reserved Physical Qty,reserved_physical_qty,Float,,150
Sold Qty,sold_qty,Float,,150
Pending Order Qty,pending_qty,Float,,150
Unit,stock_uom,,,80
Unit Price,unit_price,Currency,,120
Net Amt,net_amount,Currency,,150
On Order (NP)Amt,on_order_np_amount,Currency,,150
Reserved Order Amt,reserved_order_amount,Currency,,150
Reserved Physical Amt,reserved_physical_amount,Currency,,150
Sold Amt,sold_amount,Currency,,150
Pending Order Amt,pending_amount,Currency,,150
Currency,currency,,,90
Requested Ship Dt(CRD),requested_ship_date,Date,,150
Confirmed Ship Dt(EDA),confirmed_ship_date,Date,,150
Special Remarks(Line Level),special_remarks,,,150
Business Unit(Sourcing),tsoi_cost_center,,,150
Purchaser,purchaser,,,150
Purchaser Comment,purchaser_comment_cf,,,150
Order Status,so_status,,,150
Delivery Status,delivery_status,,,150
Billing Status,billed_status,,,150
Sales Order,sales_order,Link,Sales Order,150
EPO No,purchase_order,Link,Purchase Order,150
EPR No,purchase_receipt,Link,Purchase Receipt,150
Material Receipt Dt,material_receipt_date,,,150
Sales Invoice #,invoice_no,Link,Sales Invoice,150
Invoice Dt,invoice_date,,,150
IRN No,irn,,,150
E-Way Bill No,ewaybill,,,150
Transporter Agency,transporter_agency,,,150
AWB #,awb_no,,,150
Stock days(Stock Qty),stock_days_for_stock_qty,,,150
Stock days(Sold Qty),stock_days_for_sold_qty,,,150
Business Type,business_type,,,150
Business Unit(TL/Product Group),parent_cost_center,,,150
Business Unit(Product),grand_parent_cost_center,,,150
Sales Person,sales_tracked_to,,,150
RSM Person,parent_sales_person,,,150
Business Unit(Sales),grand_parent_sales_person,,,150
Customer Group,customer_group,Link,Customer Group,150
Territory,territory,Link,Territory,150
Industry,industry,Data,,150
Customer Payment Term,payment_terms_template,,,180"""
    )


def get_conditions(filters):
    conditions = []
    # conditions.append(" tso.name = 'SAL-ORD-2022-00011' ")

    if filters.so_status:
        if filters.so_status == "Open":
            conditions.append(
                "tso.status in ('To Deliver','To Deliver and Bill', 'To Bill', 'On Hold')"
            )
        elif filters.so_status == "Closed":
            conditions.append("tso.status in ('Closed', 'Completed')")
    return conditions and " and " + " and ".join(conditions) or ""


def csv_to_columns(csv_str):
    props = ["label", "fieldname", "fieldtype", "options", "width"]
    return [zip(props, col.split(",")) for col in csv_str.split("\n")]
