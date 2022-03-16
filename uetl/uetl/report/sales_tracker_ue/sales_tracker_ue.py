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
            -- tso.po_date  customer_po_date, 
            DATE_FORMAT(tso.po_date,'%d/%m/%Y')  customer_po_date, 
            DATE_FORMAT(tso.creation,'%d/%m/%Y %H:%i') so_creation,
            tsoi.cpo_line_no_cf as cpo_line_no_cf,
            tsoi.external_part_no_cf as external_part_no_cf,
            tsoi.item_name item_number, 
            tsoi.brand mfr, 
            tsoi.stock_qty cpo_qty,
            tsoi.stock_qty - tsoi.ordered_qty on_order_np_qty ,
            tsoi.ordered_qty - coalesce(tpoi.received_qty,0) reserved_order_qty ,
            tsoi.ordered_qty - tsoi.delivered_qty - (coalesce(tpoi.stock_qty,0) - coalesce(tpoi.received_qty,0)) reserved_physical_qty ,
            tsoi.delivered_qty sold_qty ,
            tsoi.stock_uom unit, 
            tsoi.base_net_rate unit_price, 
            tsoi.base_net_amount net_amount ,
            tsoi.base_net_rate * (tsoi.stock_qty - tsoi.ordered_qty) on_order_np_amount,
            tsoi.base_net_rate * (tsoi.ordered_qty - coalesce(tpoi.received_qty,0)) reserved_order_amount,
            tsoi.base_net_rate * (tsoi.ordered_qty - tsoi.delivered_qty 
                - (coalesce(tpoi.stock_qty,0) - coalesce(tpoi.received_qty,0))) reserved_physical_amount,
            tsoi.base_net_rate * (tsoi.delivered_qty) sold_amount, 
            tso.currency , 
            DATE_FORMAT(tsoi.delivery_date,'%d-%b-%Y') requested_ship_date, 
            DATE_FORMAT(tpoi.expected_delivery_date,'%d-%b-%Y') confirmed_ship_date ,
            tsoi.special_remarks_cf as special_remarks,
            tpoi.cost_center  as sourcing,
            tpoi.owner as purchaser,
            tsii.parent as invoice_no,
            DATE_FORMAT(tsii.posting_date, '%d-%b-%Y') as invoice_date,
            tsii.stock_qty as si_qty,
            tsii.transporter as transporter_agency,
            tsii.lr_no as awb_no,
            tpri.posting_date  as material_receipt_date ,
            tpri.batch_no pr_item_batch_no, 
            tsii.batch_no si_item_batch_no,
            CASE tb.batch_qty WHEN 0 THEN 0 ELSE DATEDIFF(NOW(),tpri.posting_date) END as stock_days_for_stock_qty,
            DATEDIFF(tsii.posting_date,tpri.posting_date) stock_days_for_sold_qty,
            tso.name sales_order ,
            tso.contact_display customer_buyer ,
            tsoi.business_type_cf business_type ,
            tpoi.purchaser_comment_cf purchaser_comment ,
            tsoi.cost_center business_unit ,
            tst.sales_person sales_tracker_to ,
            tc.customer_group customer_group ,
            tc.industry industry,
            tso.territory territory 
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
            -- tpri.posting_date 'tpr_posting_date', tpri.batch_no 'tpri_batch_no', tpri.item_code 'tpri_item_code',
            -- tsii.posting_date 'tsi_posting_date', tsii.batch_no 'tsii_batch_no', tsii.item_code 'tsii_item_code'
        from 
            `tabSales Order` tso
        inner join `tabSales Order Item` tsoi on tsoi.parent = tso.name 
        inner join tabItem ti on ti.name = tsoi.item_code and ti.is_stock_item = 0
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
        left outer join (
            select 
                tpri.parent, tpri.name, tpr.posting_date,
                tpri.purchase_order, tpri.purchase_order_item, tpri.batch_no, tpri.item_code
            from  `tabPurchase Receipt` tpr 
            inner join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name
            where tpr.docstatus = 1
        ) tpri on tpri.purchase_order = tpoi.parent 
            and tpri.purchase_order_item = tpoi.name 
        left outer join `tabBatch` tb  on tpri.batch_no  = tb.name
        left outer join (
            select 
                tsii.parent, tsii.name, tsi.posting_date, tsi.transporter,
                tsii.sales_order, tsii.so_detail, tsii.batch_no, tsii.item_code, tsii.stock_qty, tsi.lr_no
            from  `tabSales Invoice` tsi 
            inner join  `tabSales Invoice Item` tsii on tsii.parent = tsi.name
            where tsi.docstatus = 1
        ) tsii on tsii.sales_order = tsoi.parent 
            and tsii.so_detail = tsoi.name and tsii.batch_no = tpri.batch_no
        left outer join tabCustomer tc on tc.name = tso.customer
        left outer join (
            select parent, sales_person  from `tabSales Team` tst 
            group by parent
        ) tst on tst.parent = tso.name
        WHERE 
            tso.docstatus = 1 -- and tso.name = 'SAL-ORD-2022-00011'
        order by 
            tso.name, tsoi.idx, tpri.item_code, tsii.item_code , tpri.batch_no , tsii.batch_no  
        """,
        as_dict=True,
        # debug=True,
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
    columns = [
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "width": 170,
            # "fieldtype": "Link",
            # "options": "Customer",
        },
        {"label": _("Customer Reference (CPO #)"), "fieldname": "cpo_no", "width": 140},
        {
            "label": _("Cust PO Dt"),
            # "fieldtype": "Date",
            "fieldname": "customer_po_date",
            "width": 110,
        },
        {
            "label": _("SO Created On"),
            # "fieldtype": "Date",
            "fieldname": "so_creation",
            "width": 140,
        },
        {"label": _("CPO Line #"), "fieldname": "cpo_line_no_cf", "width": 100},
        {
            "label": _("External Part #"),
            "fieldname": "external_part_no_cf",
            "width": 130,
        },
        {"label": _("Item #"), "fieldname": "item_number", "width": 110},
        {"label": _("MFR"), "fieldname": "mfr", "width": 60},
        {
            "label": _("CPO Qty"),
            "fieldtype": "Float",
            "fieldname": "cpo_qty",
            "width": 100,
        },
        {
            "label": _("On Order (NP)QTY"),
            "fieldtype": "Float",
            "fieldname": "on_order_np_qty",
            "width": 140,
        },
        {
            "label": _("Reserved Order Qty"),
            "fieldtype": "Float",
            "fieldname": "reserved_order_qty",
            "width": 160,
        },
        {
            "label": _("Reserved Physical Qty"),
            "fieldtype": "Float",
            "fieldname": "reserved_physical_qty",
            "width": 170,
        },
        {
            "label": _("Sold Qty"),
            "fieldtype": "Float",
            "fieldname": "sold_qty",
            "width": 100,
        },
        {
            "label": _("Unit"),
            "fieldtype": "Link",
            "fieldname": "unit",
            "options": "UOM",
            "width": 60,
        },
        {
            "label": _("Unit Price"),
            "fieldtype": "Currency",
            "fieldname": "unit_price",
            "options": "currency",
            "width": 100,
        },
        {
            "label": _("Net Amt"),
            "fieldtype": "Currency",
            "fieldname": "net_amount",
            "options": "currency",
            "width": 120,
        },
        {
            "label": _("On Order (NP)Amt"),
            "fieldtype": "Currency",
            "fieldname": "on_order_np_amount",
            "options": "currency",
            "width": 140,
        },
        {
            "label": _("Reserved Order Amt"),
            "fieldtype": "Currency",
            "fieldname": "reserved_order_amount",
            "options": "currency",
            "width": 160,
        },
        {
            "label": _("Reserved Physical Amt"),
            "fieldtype": "Currency",
            "fieldname": "reserved_physical_amount",
            "options": "currency",
            "width": 180,
        },
        {
            "label": _("Sold Amt"),
            "fieldtype": "Currency",
            "fieldname": "sold_amount",
            "options": "currency",
            "width": 120,
        },
        {
            "label": _("Currency"),
            "fieldtype": "Link",
            "fieldname": "currency",
            "options": "Currency",
            "width": 100,
        },
        {
            "label": _("Requested Ship Dt(CRD)"),
            # "fieldtype": "Date",
            "fieldname": "requested_ship_date",
            "width": 180,
        },
        {
            "label": _("Confirmed Ship Dt(EDA)"),
            # "fieldtype": "Date",
            "fieldname": "confirmed_ship_date",
            "width": 180,
        },
        {
            "label": _("Special Remarks(Line Level)"),
            "fieldname": "special_remarks",
            "width": 200,
        },
        {
            "label": _("Sourcing"),
            "fieldtype": "Link",
            "fieldname": "sourcing",
            "options": "Cost Center",
            "width": 100,
        },
        {
            "label": _("Purchaser"),
            "fieldtype": "Link",
            "fieldname": "purchaser",
            "options": "User",
            "width": 150,
        },
        {
            "label": _("Invoice #"),
            "fieldtype": "Link",
            "fieldname": "invoice_no",
            "options": "Sales Invoice",
            "width": 120,
        },
        {
            "label": _("Invoice Dt"),
            # "fieldtype": "Date",
            "fieldname": "invoice_date",
            "width": 100,
        },
        {
            "label": _("Transporter Agency"),
            "fieldtype": "Link",
            "fieldname": "transporter_agency",
            "options": "Supplier",
            "width": 200,
        },
        {"label": _("AWB #"), "fieldname": "awb_no", "width": 120},
        {
            "label": _("Material Receipt Dt"),
            "fieldtype": "Date",
            "fieldname": "material_receipt_date",
            "width": 150,
        },
        {
            "label": _("Stock days(Stock Qty)"),
            "fieldtype": "Int",
            "fieldname": "stock_days_for_stock_qty",
            "width": 180,
        },
        {
            "label": _("Stock days(Sold Qty)"),
            "fieldtype": "Int",
            "fieldname": "stock_days_for_sold_qty",
            "width": 160,
        },
        {
            "label": _("Sales Order"),
            "fieldtype": "Link",
            "fieldname": "sales_order",
            "options": "Sales Order",
            "width": 170,
        },
        {
            "label": _("Customer Buyer"),
            "fieldtype": "Link",
            "fieldname": "customer_buyer",
            "options": "Contact",
            "width": 130,
        },
        {"label": _("Business Type"), "fieldname": "business_type", "width": 110},
        {
            "label": _("Purchaser Comment"),
            "fieldname": "purchaser_comment",
            "width": 180,
        },
        {
            "label": _("Business Unit(Sourcing)"),
            "fieldtype": "Link",
            "fieldname": "business_unit",
            "options": "Cost Center",
            "width": 170,
        },
        {
            "label": _("Sales Tracked To"),
            "fieldtype": "Link",
            "fieldname": "sales_tracker_to",
            "options": "Sales Person",
            "width": 130,
        },
        {
            "label": _("Customer Group"),
            "fieldtype": "Link",
            "fieldname": "customer_group",
            "options": "Customer Group",
            "width": 130,
        },
        {
            "label": _("Industry"),
            "fieldname": "industry",
            "width": 90,
        },
        {
            "label": _("Territory"),
            "fieldtype": "Link",
            "fieldname": "territory",
            "options": "Territory",
            "width": 90,
        },
    ]

    return columns
