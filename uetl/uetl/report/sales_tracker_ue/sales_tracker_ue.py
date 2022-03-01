# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	return get_columns(filters), get_data(filters)

def get_data(filters=None):
    data_result = frappe.db.sql(
        """SELECT  
ROW_NUMBER()over(PARTITION by SO.name,PO_item.sales_order,SI_item.sales_order) as row_no,        
SO.customer as customer,
SO.po_no as cpo_no,
SO.po_date as cust_po_date,
DATE(SO.creation) as so_created_on,
SO_item.cpo_line_no_cf as cpo_line_no,
SO_item.external_part_no_cf as external_part_no,
SO_item.item_name as item_number,
SO_item.brand as mfr,
SO_item.qty as cpo_qty, 
(SO_item.qty-SO_item.ordered_qty) as np_qty,
SO_item.qty-(SO_item.qty-SO_item.ordered_qty)-PR_item.received_qty  as reserved_order_qty,
SO_item.qty-(SO_item.qty-SO_item.ordered_qty)-(PO_item.stock_qty - PO_item.received_qty)-SO_item.delivered_qty  as reserved_physical_qty,
SO_item.delivered_qty as sold_qty,
SO_item.uom as unit,
SO_item.rate as unit_price,
SO_item.amount as net_amt,
(SO_item.qty-SO_item.ordered_qty)*SO_item.rate as np_amt,
(SO_item.qty-(SO_item.qty-SO_item.ordered_qty)-PR_item.received_qty)*SO_item.rate as reserved_order_amt,
(SO_item.qty-(SO_item.qty-SO_item.ordered_qty)-(PO_item.stock_qty - PO_item.received_qty)-SO_item.delivered_qty)*SO_item.rate  as reserved_physical_amt,
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
on PO_item.sales_order = SO.name and PO_item.item_code =SO_item.item_code  and PO_item.schedule_date =SO_item.delivery_date and PO_item.docstatus=1
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
order by SO.name,SO_item.item_code,SO_item.cpo_line_no_cf

""",debug=True,as_dict=True)

    empty_cols=['customer','cpo_no','cust_po_date','so_created_on','cpo_line_no','external_part_no','item_number','mfr','cpo_qty','np_qty','reserved_order_qty','reserved_physical_qty',
'sold_qty','unit','unit_price','net_amt','np_amt','reserved_order_amt','reserved_physical_amt','sold_amt','currency','requested_ship_date','special_remarks','invoice_no','invoice_date','transporter_agency', 'awb_no','material_receipt_date','stock_days_for_stock_qty','stock_days_for_sold_qty','sales_order',
'buyer','business_type','business_unit','sales_tracked_to','customer_group','customer_master','territory']

    new_data_result=[]
    for data in data_result:
        if data.row_no > 1:
            for col in empty_cols:
                data.update({col:None})
            new_data_result.append(data)
        else:
            new_data_result.append(data)

    return new_data_result



def get_columns(filters):
    columns = [
        {
            "label": _("row_n0"),
            "fieldtype": "Int",
            "fieldname": "row_no",
            "width": 40
        },        
        {
            "label": _("Customer"),
            "fieldtype": "Link",
            "fieldname": "customer",
            "options": "Customer",
            "width": 170
        },
        {
            "label": _("CPO#"),
            "fieldname": "cpo_no",
            "width": 100
        },
        {
            "label": _("Cust PO Dt"),
            "fieldtype": "Date",
            "fieldname": "cust_po_date",
            "width": 110
        },
        {
            "label": _("SO Created On"),
            "fieldtype": "Date",
            "fieldname": "so_created_on",
            "width": 120
        },	
        {
            "label": _("CPO Line #"),
            "fieldname": "cpo_line_no",
            "width": 100
        },
        {
            "label": _("External Part #"),
            "fieldname": "external_part_no",
            "width": 130
        },		
       {
            "label": _("Item #"),
            "fieldname": "item_number",
            "width": 110
        },	
       {
            "label": _("MFR"),
            "fieldname": "mfr",
            "width": 60
        },
        {
            "label": _("CPO Qty"),
            "fieldtype": "Float",
            "fieldname": "cpo_qty",
            "width": 100
        },	
        {
            "label": _("On Order (NP)QTY"),
            "fieldtype": "Float",
            "fieldname": "np_qty",
            "width": 140
        },		
        {
            "label": _("Reserved Order Qty"),
            "fieldtype": "Float",
            "fieldname": "reserved_order_qty",
            "width": 160
        },
        {
            "label": _("Reserved Physical Qty"),
            "fieldtype": "Float",
            "fieldname": "reserved_physical_qty",
            "width": 170
        },
        {
            "label": _("Sold Qty"),
            "fieldtype": "Float",
            "fieldname": "sold_qty",
            "width": 100
        },																			
        {
            "label": _("Unit"),
            "fieldtype": "Link",
            "fieldname": "unit",
            "options": "UOM",
            "width": 60
        },
        {
            "label": _("Unit Price"),
            "fieldtype": "Currency",
            "fieldname": "unit_price",
            "options": "currency",
            "width": 100
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
            "width": 140
        },
        {
            "label": _("Reserved Order Amt"),
            "fieldtype": "Currency",
            "fieldname": "reserved_order_amt",
            "options": "currency",
            "width": 160
        },
        {
            "label": _("Reserved Physical Amt"),
            "fieldtype": "Currency",
            "fieldname": "reserved_physical_amt",
            "options": "currency",
            "width": 180
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
            "width": 100
        },	
        {
            "label": _("Requested Ship Dt(CRD)"),
            "fieldtype": "Date",
            "fieldname": "requested_ship_date",
            "width": 180
        },
        {
            "label": _("Confirmed Ship Dt(EDA)"),
            "fieldtype": "Date",
            "fieldname": "confirmed_ship_date",
            "width": 180
        },
       {
            "label": _("Special Remarks(Line Level)"),
            "fieldname": "special_remarks",
            "width": 200
        },	
        {
            "label": _("Sourcing"),
            "fieldtype": "Link",
            "fieldname": "sourcing",
            "options": "Cost Center",
            "width": 100
        },		
        {
            "label": _("Purchaser"),
            "fieldtype": "Link",
            "fieldname": "purchaser",
            "options": "User",
            "width": 150
        },	
        {
            "label": _("Invoice #"),
            "fieldtype": "Link",
            "fieldname": "invoice_no",
            "options": "Sales Invoice",
            "width": 120
        },	
        {
            "label": _("Invoice Dt"),
            "fieldtype": "Date",
            "fieldname": "invoice_date",
            "width": 100
        },		
        {
            "label": _("Transporter Agency"),
            "fieldtype": "Link",
            "fieldname": "transporter_agency",
            "options": "Supplier",
            "width": 200
        },		
       {
            "label": _("AWB #"),
            "fieldname": "awb_no",
            "width": 120
        },	
        {
            "label": _("Material Receipt Dt"),
            "fieldtype": "Date",
            "fieldname": "material_receipt_date",
            "width": 150
        },		
        {
            "label": _("Stock days(Stock Qty)"),
            "fieldtype": "Int",
            "fieldname": "stock_days_for_stock_qty",
            "width": 180
        },	
        {
            "label": _("Stock days(Sold Qty)"),
            "fieldtype": "Int",
            "fieldname": "stock_days_for_sold_qty",
            "width": 160
        },			
        {
            "label": _("Sales Order"),
            "fieldtype": "Link",
            "fieldname": "sales_order",
            "options": "Sales Order",
            "width": 170
        },
        {
            "label": _("Customer Buyer"),
            "fieldtype": "Link",
            "fieldname": "buyer",
            "options": "Contact",
            "width": 130
        },	
       {
            "label": _("Business Type"),
            "fieldname": "business_type",
            "width": 110
        },	
       {
            "label": _("Purchaser Comment"),
            "fieldname": "purchaser_comment",
            "width": 180
        },		
        {
            "label": _("Business Unit(Sourcing)"),
            "fieldtype": "Link",
            "fieldname": "business_unit",
            "options": "Cost Center",
            "width": 170
        },		
       {
            "label": _("Sales Tracked To"),
            "fieldtype": "Link",
            "fieldname": "sales_tracked_to",
            "options": "Sales Person",
            "width": 130
        },		
       {
            "label": _("Customer Group"),
            "fieldtype": "Link",
            "fieldname": "customer_group",
            "options": "Customer Group",
            "width": 130
        },		
       {
            "label": _("Industry"),
            "fieldtype": "Link",
            "fieldname": "customer_master",
            "options": "Industry Type",
            "width": 90
        },			
        {
            "label": _("Territory"),
            "fieldtype": "Link",
            "fieldname": "territory",
            "options": "Territory",
            "width": 90
        }																								
    ]

    return columns	