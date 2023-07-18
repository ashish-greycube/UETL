import frappe


def execute():
    print("Set sales order reference in purchase receipt items")
    frappe.db.sql(
        """
        update `tabPurchase Receipt Item` tpri 
            inner join `tabPurchase Order Item` tpoi on tpoi.name = tpri.purchase_order_item 
            and tpoi.parent = tpri.purchase_order 
        set 
            tpri.sales_order_cf = tpoi.sales_order , 
            tpri.sales_order_item_cf = tpoi.sales_order_item
        where nullif(tpri.sales_order_item_cf,'')  is null 
                  """
    )
