# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	return get_columns(filters), get_data(filters)

def get_data(filters=None):
	data = frappe.db.sql(
        """SELECT  
SO.customer as customer,
SO.po_no as cpo_no,
SO.po_date as cust_po_date,
SO.creation as so_created_on,
SO_item.cpo_line_no_cf as cpo_line_no,
SO_item.external_part_no_cf as external_part_no,
SO_item.item_name as item_number,
SO_item.brand as mfr,
SO_item.qty as cpo_qty, 
PO_item.qty as np_qty,
SO_item.qty-(SO_item.qty-PO_item.qty)-PR_item.qty  as reserved_order_qty,
SO_item.qty-(SO_item.qty-PO_item.qty)-(PO_item.qty-PO_item.received_qty)-SO_item.delivered_qty  as reserved_physical_qty,
SO_item.delivered_qty as sold_qty,
SO_item.uom as unit,
SO_item.rate as unit_price,
SO_item.amount as net_amt,
(SO_item.qty-PO_item.qty)*SO_item.rate as np_amt,
(SO_item.qty-(SO_item.qty-PO_item.qty)-PR_item.qty)*SO_item.rate as reserved_order_amt,
(SO_item.qty-(SO_item.qty-PO_item.qty)-(PO_item.qty-PO_item.received_qty)-SO_item.delivered_qty)*SO_item.rate  as reserved_physical_amt,
SO_item.delivered_qty*SO_item.rate as sold_amt,
SO.currency ,
SO_item.delivery_date  as requested_ship_date,
PO_item.expected_delivery_date  as confirmed_ship_date,
SO_item.special_remarks_cf as special_remarks,
PO_item.cost_center  as sourcing,
PO_item.owner as purchaser,
SI_item.parent as invoice_no,
SI.posting_date as invoice_date,
SI.transporter as transporter_agency,
SI.irn as awb_no,
PR.posting_date  as material_receipt_date,
DATEDIFF(CURDATE() ,PR.posting_date) as stock_days_for_stock_qty,
DATEDIFF(SI.posting_date,PR.posting_date) as stock_days_for_sold_qty,
SO.name as sales_order,
SO.contact_person as buyer,
SO_item.business_type_cf as business_type,
PO_item.purchaser_comment_cf  as purchaser_comment,
SO_item.cost_center  as business_unit,
ST.sales_person as sales_tracked_to,
SO.customer_group as customer_group ,
Cust.industry  as customer_master,
SO.territory as territory 
FROM `tabSales Order` SO inner join `tabSales Order Item` SO_item 
on SO.name=SO_item.parent  and SO.docstatus=1
left outer join `tabPurchase Order Item` PO_item 
on PO_item.item_code =SO_item.item_code  and PO_item.schedule_date =SO_item.delivery_date and PO_item.docstatus=1
left outer join `tabPurchase Receipt Item` PR_item 
on PR_item.purchase_order =SO.po_no and PR_item.item_code =SO_item.item_code
left outer join `tabSales Invoice Item` as SI_item 
on SI_item.sales_order =SO.name and SI_item.so_detail=SO_item.name 
left outer join `tabSales Invoice` as SI
on SI.name=SI_item.parent and SI.docstatus=1
left outer join `tabPurchase Receipt` as PR 
on PR.name=PR_item.parent  and PR.docstatus=1
left outer join `tabCustomer` as Cust
on SO.customer=Cust.name 
left outer join `tabSales Team` as ST on ST.name =(select ST.name from `tabSales Team` as ST inner join `tabSales Order` SO on SO.name=ST.parent order by ST.idx ASC limit 1 )
order by SO.name

""")
	return data



def get_columns(filters):
    columns = [
        {
            "label": _("Customer"),
            "fieldtype": "Link",
            "fieldname": "customer",
            "options": "Customer",
            "width": 200
        },
        {
            "label": _("CPO#"),
            "fieldname": "cpo_no",
            "width": 200
        },
        {
            "label": _("Cust PO Dt"),
            "fieldtype": "Date",
            "fieldname": "cust_po_date",
            "width": 140
        },
        {
            "label": _("SO Created On"),
            "fieldtype": "Date",
            "fieldname": "so_created_on",
            "width": 140
        },	
        {
            "label": _("CPO Line #"),
            "fieldname": "cpo_line_no",
            "width": 220
        },
        {
            "label": _("External Part #"),
            "fieldname": "external_part_no",
            "width": 220
        },		
       {
            "label": _("Item #"),
            "fieldname": "item_number",
            "width": 220
        },	
       {
            "label": _("MFR"),
            "fieldname": "mfr",
            "width": 220
        },
        {
            "label": _("CPO Qty"),
            "fieldtype": "Float",
            "fieldname": "cpo_qty",
            "width": 120
        },	
        {
            "label": _("On Order (NP)QTY"),
            "fieldtype": "Float",
            "fieldname": "np_qty",
            "width": 120
        },		
        {
            "label": _("Reserved Order Qty"),
            "fieldtype": "Float",
            "fieldname": "reserved_order_qty",
            "width": 120
        },
        {
            "label": _("Reserved Physical Qty"),
            "fieldtype": "Float",
            "fieldname": "reserved_physical_qty",
            "width": 120
        },
        {
            "label": _("Sold Qty"),
            "fieldtype": "Float",
            "fieldname": "sold_qty",
            "width": 120
        },																			
        {
            "label": _("Unit"),
            "fieldtype": "Link",
            "fieldname": "unit",
            "options": "UOM",
            "width": 220
        },
        {
            "label": _("Unit Price"),
            "fieldtype": "Currency",
            "fieldname": "unit_price",
            "options": "currency",
            "width": 120
        },		
        {
            "label": _("Net Amt"),
            "fieldtype": "Currency",
            "fieldname": "net_amt",
            "options": "currency",
            "width": 120
        },
        {
            "label": _("On Order (NP)Amt"),
            "fieldtype": "Currency",
            "fieldname": "np_amt",
            "options": "currency",
            "width": 120
        },
        {
            "label": _("Reserved Order Amt"),
            "fieldtype": "Currency",
            "fieldname": "reserved_order_amt",
            "options": "currency",
            "width": 120
        },
        {
            "label": _("Reserved Physical Amt"),
            "fieldtype": "Currency",
            "fieldname": "reserved_physical_amt",
            "options": "currency",
            "width": 120
        },		
        {
            "label": _("Sold Amt"),
            "fieldtype": "Currency",
            "fieldname": "sold_amt",
            "options": "currency",
            "width": 120
        },
        {
            "label": _("Currency"),
            "fieldtype": "Link",
            "fieldname": "currency",
            "options": "Currency",
            "width": 220
        },	
        {
            "label": _("Requested Ship Dt(CRD)"),
            "fieldtype": "Date",
            "fieldname": "requested_ship_date",
            "width": 140
        },
        {
            "label": _("Confirmed Ship Dt(EDA)"),
            "fieldtype": "Date",
            "fieldname": "confirmed_ship_date",
            "width": 140
        },
       {
            "label": _("Special Remarks(Line Level)"),
            "fieldname": "special_remarks",
            "width": 220
        },	
        {
            "label": _("Sourcing"),
            "fieldtype": "Link",
            "fieldname": "sourcing",
            "options": "Cost Center",
            "width": 220
        },		
        {
            "label": _("Purchaser"),
            "fieldtype": "Link",
            "fieldname": "purchaser",
            "options": "User",
            "width": 220
        },	
        {
            "label": _("Invoice #"),
            "fieldtype": "Link",
            "fieldname": "invoice_no",
            "options": "Sales Invoice",
            "width": 220
        },	
        {
            "label": _("Invoice Dt"),
            "fieldtype": "Date",
            "fieldname": "invoice_date",
            "width": 140
        },		
        {
            "label": _("Transporter Agency"),
            "fieldtype": "Link",
            "fieldname": "transporter_agency",
            "options": "Supplier",
            "width": 220
        },		
       {
            "label": _("AWB #"),
            "fieldname": "awb_no",
            "width": 220
        },	
        {
            "label": _("Material Receipt Dt"),
            "fieldtype": "Date",
            "fieldname": "material_receipt_date",
            "width": 140
        },		
        {
            "label": _("Stock days(Stock Qty)"),
            "fieldtype": "Int",
            "fieldname": "stock_days_for_stock_qty",
            "width": 120
        },	
        {
            "label": _("Stock days(Sold Qty)"),
            "fieldtype": "Int",
            "fieldname": "stock_days_for_sold_qty",
            "width": 120
        },			
        {
            "label": _("Sales Order"),
            "fieldtype": "Link",
            "fieldname": "sales_order",
            "options": "Sales Order",
            "width": 220
        },
        {
            "label": _("Customer Buyer"),
            "fieldtype": "Link",
            "fieldname": "buyer",
            "options": "Contact",
            "width": 220
        },	
       {
            "label": _("Business Type"),
            "fieldname": "business_type",
            "width": 220
        },	
       {
            "label": _("Purchaser Comment"),
            "fieldname": "purchaser_comment",
            "width": 220
        },		
        {
            "label": _("Business Unit(Sourcing)"),
            "fieldtype": "Link",
            "fieldname": "business_unit",
            "options": "Cost Center",
            "width": 220
        },		
       {
            "label": _("Sales Tracked To"),
            "fieldtype": "Link",
            "fieldname": "sales_tracked_to",
            "options": "Sales Person",
            "width": 220
        },		
       {
            "label": _("Customer Group"),
            "fieldtype": "Link",
            "fieldname": "customer_group",
            "options": "Customer Group",
            "width": 220
        },		
       {
            "label": _("Industry"),
            "fieldtype": "Link",
            "fieldname": "customer_master",
            "options": "Industry Type",
            "width": 220
        },			
        {
            "label": _("Territory"),
            "fieldtype": "Link",
            "fieldname": "territory",
            "options": "Territory",
            "width": 220
        }																								
    ]

    return columns	