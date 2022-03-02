from __future__ import unicode_literals
import frappe, erpnext, json
from frappe import _

def validate_for_duplicate_items_based_on_date(self,method):
    if self.doctype=='Sales Order':
        date_field='delivery_date'
    elif self.doctype=='Purchase Order':
        date_field='schedule_date'

    chk_dupl_itm = []
    for d in self.get('items'):
        if {"item_code":d.item_code,"date":d.get(date_field)} in chk_dupl_itm:
            frappe.throw(_("Note: Item <b>{0}</b>  with date <b>{1}</b> is entered multiple times").format(d.item_code,d.get(date_field)))
        else:
            chk_dupl_itm.append({"item_code":d.item_code,"date":d.get(date_field)})	



def set_cost_center_based_on_sales_order(self,method):
    for item in self.items:
        if not item.cost_center and item.so_detail:
            item.cost_center= frappe.db.get_value('Sales Order Item', item.so_detail, 'cost_center')           