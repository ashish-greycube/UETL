# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from itertools import groupby
from frappe.utils import cstr, cint, add_to_date, today

from uetl.uetl.report import csv_to_columns


def execute(filters=None):
    columns, data = [], []
    data = get_data(filters)
    columns = get_columns(filters, data and data[0] or None)
    return columns, data


def get_data(filters=None):
    query = """
        select 
        	tc.name customer,
            tso.customer_name , 
            tso.po_no cpo_no, 
			tso.po_date customer_po_date, 
            DATE_FORMAT(tso.creation,'%%Y-%%m-%%d %%H:%%i') so_creation,
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
            tsoi.delivery_date requested_ship_date, 
            tpoi.expected_delivery_date confirmed_ship_date ,
            tsoi.special_remarks_cf as special_remarks,
            tpoi.cost_center  as sourcing,
            tsoi.purchaser_cf as purchaser,
            tsii.parent as invoice_no,
            tsii.posting_date as invoice_date,
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
            tsii.irn , tsii.ewaybill , tsoi.delivery_date soi_delivery_date
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
        inner join tabCustomer tc on tc.name = tso.customer
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
        """

    if cint(filters.get("hide_group_fields")):
        query = SHOW_SUMMARY_SQL

    data = frappe.db.sql(
        query.format(
            conditions=get_conditions(filters),
        ),
        filters,
        as_dict=True,
    )

    if filters.get("sales_person"):
        value = filters.get("sales_person")
        data = [
            d
            for d in data
            if value in (d.sales_tracked_to or "")
            or value in (d.parent_sales_person or "")
            or value in (d.grand_parent_sales_person or "")
        ]
    if filters.get("cost_center"):
        value = filters.get("cost_center")
        data = [
            d
            for d in data
            if value in (d.tsoi_cost_center or "")
            or value in (d.parent_cost_center or "")
            or value in (d.grand_parent_cost_center or "")
        ]

    if filters.get("upg"):
        value = filters.get("upg")
        data = [d for d in data if value == d.unified_product_group_cf]

    if filters.get("mr_date"):
        data = [d for d in data if d.mr_date]

    for field in (
        "on_order_np_qty",
        "reserved_order_qty",
        "reserved_physical_qty",
        "sold_qty",
    ):
        if filters.get(field) == "> 0":
            data = [d for d in data if d.get(field) > 0]
        elif filters.get(field) == "= 0":
            data = [d for d in data if d.get(field) == 0]

    return data or []


def get_columns(filters, item):
    columns = (
        cint(filters.get("hide_group_fields")) and SHOW_SUMMARY_COLUMNS
    ) or COLUMNS

    return csv_to_columns("\n".join(columns))


def get_conditions(filters):
    conditions = []
    # conditions.append(" tso.name = 'ESO2201186' ")

    if filters.so_status:
        if filters.so_status == "Open":
            conditions.append(
                "tso.status in ('To Deliver','To Deliver and Bill', 'To Bill', 'On Hold')"
            )
        elif filters.so_status == "Closed":
            conditions.append("tso.status in ('Closed', 'Completed')")

    if filters.get("customer"):
        conditions.append("tc.name = %(customer)s")

    if filters.get("territory"):
        conditions.append("tc.territory = %(territory)s")

    if filters.get("brand") and not cint(filters.get("hide_group_fields")):
        conditions.append("ti.brand = %(brand)s")

    if filters.get("mr_date") == "Yesterday":
        conditions.append("tpri.posting_date = %s" % add_to_date(today(), days=-1))

    if filters.get("mr_date") == "Today":
        conditions.append("tpri.posting_date = %s" % today())

    return conditions and " and " + " and ".join(conditions) or ""


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_upg(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """ select 
                distinct unified_product_group_cf from tabBrand tb
            where name like %(brand)s and unified_product_group_cf like %(txt)s 
        limit %(start)s, %(page_len)s""",
        {
            "start": start,
            "page_len": page_len,
            "txt": "%%%s%%" % txt,
            "brand": "%%%s%%" % filters.get("brand", ""),
        },
    )


COLUMNS = [
    "Customers Name,customer_name,,,150",
    "Customer Buyer,customer_buyer,,,150",
    "Customer Reference (CPO #),cpo_no,,,150",
    "Cust PO Dt,customer_po_date,Date,,150",
    "SO Created On,so_creation,DateTime,,150",
    "CPO Line #,cpo_line_no_cf,,,150",
    "External Part #,external_part_no_cf,,,150",
    "Item Code,item_code,Link,Item,150",
    "Item #,item_number,,,150",
    "Item Group,item_group,Link,Item Group,150",
    "UPG,unified_product_group_cf,,,150",
    "MFR,mfr,Data,,150",
    "CPO Qty,cpo_qty,Float,,150",
    "On Order (NP)QTY,on_order_np_qty,Float,,150",
    "Reserved Order Qty,reserved_order_qty,Float,,150",
    "Reserved Physical Qty,reserved_physical_qty,Float,,150",
    "Sold Qty,sold_qty,Float,,150",
    "Pending Order Qty,pending_qty,Float,,150",
    "Unit,stock_uom,,,80",
    "Unit Price,unit_price,Currency,,120",
    "Net Amt,net_amount,Currency,,150",
    "On Order (NP)Amt,on_order_np_amount,Currency,,150",
    "Reserved Order Amt,reserved_order_amount,Currency,,150",
    "Reserved Physical Amt,reserved_physical_amount,Currency,,150",
    "Sold Amt,sold_amount,Currency,,150",
    "Pending Order Amt,pending_amount,Currency,,150",
    "Currency,currency,,,90",
    "Requested Ship Dt(CRD),requested_ship_date,Date,,150",
    "Confirmed Ship Dt(EDA),confirmed_ship_date,Date,,150",
    "Earliest Ship Dt(EDA),earliest_eda,Date,,150",
    "Farthest Ship Dt(EDA),farthest_eda,Date,,150",
    "Special Remarks(Line Level),special_remarks,,,150",
    "Business Unit(Sourcing),tsoi_cost_center,,,150",
    "Purchaser,purchaser,,,150",
    "Purchaser Comment,purchaser_comment_cf,,,150",
    "Order Status,so_status,,,150",
    "Delivery Status,delivery_status,,,150",
    "Billing Status,billed_status,,,150",
    "Sales Order,sales_order,Link,Sales Order,150",
    "EPO No,purchase_order,Link,Purchase Order,150",
    "EPR No,purchase_receipt,Link,Purchase Receipt,150",
    "Material Receipt Dt,material_receipt_date,Date,,150",
    "Sales Invoice #,invoice_no,Link,Sales Invoice,150",
    "Invoice Dt,invoice_date,Date,,150",
    "IRN No,irn,,,150",
    "E-Way Bill No,ewaybill,,,150",
    "Transporter Agency,transporter_agency,,,150",
    "AWB #,awb_no,,,150",
    "Stock days(Stock Qty),stock_days_for_stock_qty,,,150",
    "Stock days(Sold Qty),stock_days_for_sold_qty,,,150",
    "Business Type,business_type,,,150",
    "Business Unit(TL/Product Group),parent_cost_center,,,150",
    "Business Unit(Product),grand_parent_cost_center,,,150",
    "Sales Person,sales_tracked_to,,,150",
    "RSM Person,parent_sales_person,,,150",
    "Business Unit(Sales),grand_parent_sales_person,,,150",
    "Customer Group,customer_group,Link,Customer Group,150",
    "Territory,territory,Link,Territory,150",
    "Industry,industry,Data,,150",
    "Customer Payment Term,payment_terms_template,,,180",
]


SHOW_SUMMARY_SQL = """
select 
    case when delivered_qty = 0 then 'Not Delivered'
                when qty = delivered_qty then 'Fully Delivered'
                when qty > delivered_qty then 'Partly Delivered'
                else '' end delivery_status ,	
    case when billed_amt = 0 then 'Not Billed'
        when billed_amt < base_net_amount then 'Partly Billed'
        when billed_amt = base_net_amount then 'Fully Billed'
        else '' end  billed_status,
tpoi.cost_center sourcing ,
so.ordered_qty - coalesce(tpoi.received_qty,0) reserved_order_qty ,
(so.ordered_qty - so.delivered_qty - tpoi.stock_qty + tpoi.received_qty) reserved_physical_qty ,
base_net_rate * (ordered_qty - coalesce(received_qty,0)) reserved_order_amount ,
base_net_rate * (so.ordered_qty - so.delivered_qty - tpoi.stock_qty + tpoi.received_qty) reserved_physical_amount ,
tpoi.earliest_eda , tpoi.farthest_eda , 
so.* 
from 
(      
    select 
    sum(tsoi.qty) qty ,
    sum(tsoi.stock_qty) cpo_qty ,
    sum(tsoi.stock_qty - tsoi.ordered_qty) on_order_np_qty ,
    sum(tsoi.delivered_qty) sold_qty ,
    sum(tsoi.stock_qty - tsoi.delivered_qty) pending_qty ,       
    sum(base_net_rate * (tsoi.stock_qty - tsoi.delivered_qty)) pending_amount ,
    sum(tsoi.ordered_qty) ordered_qty , 
    sum(tsoi.delivered_qty) delivered_qty ,
    sum(tsoi.base_net_rate * tsoi.delivered_qty) sold_amount ,
    sum(tsoi.billed_amt) billed_amt ,
    sum(tsoi.base_net_amount) base_net_amount ,
    sum(tsoi.base_net_rate * (tsoi.stock_qty - tsoi.ordered_qty)) on_order_np_amount,
    avg(tsoi.base_net_rate) base_net_rate , 
    tc.name customer ,
    tso.customer_name,
    tso.contact_display customer_buyer,
    tso.po_no cpo_no,
    tso.po_date customer_po_date,
    DATE(tso.creation) so_creation,
    tsoi.delivery_date requested_ship_date, 
    tsoi.cpo_line_no_cf,
    external_part_no_cf,
    tsoi.item_code,
    tsoi.item_group,
    tsoi.item_name item_number,
    unified_product_group_cf,
    tsoi.brand mfr,
	tso.currency,
    tsoi.purchaser_cf purchaser,
    group_concat(distinct tsoi.cost_center) tsoi_cost_center ,
    tso.status so_status,
    tso.name sales_order,
    tsoi.business_type_cf business_type,
    tccp.parent_cost_center ,
    tccgp.parent_cost_center grand_parent_cost_center ,
    tst.sales_person sales_tracked_to ,
    tsp.parent_sales_person , 
    tspp.parent_sales_person grand_parent_sales_person , 
    tc.customer_group ,
    tso.territory ,
    tc.industry ,
    tso.payment_terms_template 
    from 
        `tabSales Order` tso
    inner join `tabSales Order Item` tsoi on tsoi.parent = tso.name 
    inner join tabItem ti on ti.name = tsoi.item_code and ti.is_stock_item = 1
    inner join tabCustomer tc on tc.name = tso.customer
    left outer join tabBrand tbr on tbr.name = ti.brand 
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
    group by tso.name , tsoi.item_code
) so 
left outer join (
    select 
        tpoi.sales_order, tpoi.item_code , 
        GROUP_CONCAT(distinct tpoi.cost_center) cost_center , 
        sum(tpoi.received_qty) received_qty, 
        sum(tpoi.stock_qty) stock_qty ,
        min(tpoi.expected_delivery_date) earliest_eda,
        max(tpoi.expected_delivery_date) farthest_eda 
        from  `tabPurchase Order` tpo
        inner join `tabPurchase Order Item` tpoi on tpoi.parent = tpo.name
        where tpo.docstatus = 1
        group by tpoi.sales_order , tpoi.item_code 
) tpoi on tpoi.sales_order = so.sales_order and tpoi.item_code = so.item_code             
order by so.customer, so.item_code

        """

SHOW_SUMMARY_COLUMNS = [
    "Customers Name,customer_name,,,150",
    "Customer PO No,cpo_no,,,150",
    "Cust PO Dt,customer_po_date,Date,,150",
    "Sales Order,sales_order,Link,Sales Order,150",
    "SO Created On,so_creation,Date,,150",
    "CPO Line #,cpo_line_no_cf,,,150",
    "External Part #,external_part_no_cf,,,150",
    "Part No,item_number,,,150",
    "Make,mfr,Data,,150",
    "Currency,currency,,,90",
    "Unit Price,base_net_rate,Currency,,120",
    "CPO Qty,cpo_qty,Float,,150",
    "Sold Qty,sold_qty,Float,,150",
    "Pending Qty,pending_qty,Float,,150",
    "CPO Amt,base_net_amount,Currency,,150",
    "Sold Amt,sold_amount,Currency,,150",
    "Pending Amt,pending_amount,Currency,,150",
    "Requested Ship Dt,requested_ship_date,Date,,150",
    "Earliest Ship Dt,earliest_eda,Date,,150",
    "Farthest Ship Dt,farthest_eda,Date,,150",
    "Purchaser,purchaser,,,150",
    "Sourcing / PM,tsoi_cost_center,,,150",
    "Sales Person,sales_tracked_to,,,150",
    "Order Status,so_status,,,150",
    "Delivery Status,delivery_status,,,150",
    "Billing Status,billed_status,,,150",
    "Business Type,business_type,,,150",
    "BU Product Team,parent_cost_center,,,150",
    "BU Product,grand_parent_cost_center,,,150",
    "RSM Team,parent_sales_person,,,150",
    "BU-Sales,grand_parent_sales_person,,,150",
    "Customer Group,customer_group,Link,Customer Group,150",
    "Territory,territory,Link,Territory,150",
    "Industry,industry,Data,,150",
    "Customer Payment Term,payment_terms_template,,,180",
    "Customer Buyer,customer_buyer,,,150",
    "Item Group,item_group,Link,Item Group,150",
    "UPG,unified_product_group_cf,,,150",
    "Item Code,item_code,Link,Item,150",
    "On Order Qty,on_order_np_qty,Float,,150",
    "Reserved Order Qty,reserved_order_qty,Float,,150",
    "Reserved Physical Qty,reserved_physical_qty,Float,,150",
    "On Order Amt,on_order_np_amount,Currency,,150",
    "Reserved Order Amt,reserved_order_amount,Currency,,150",
    "Reserved Physical Amt,reserved_physical_amount,Currency,,150",
]
