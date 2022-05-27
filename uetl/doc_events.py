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


def validate_so_reference_in_item(self,method):
    for item in self.items:
        if not item.sales_order_item:
            frappe.throw(_("Sales order reference is missing for <b> row {0} : Item {1}</b>").format(item.idx,item.item_code))

def set_cost_center_based_on_sales_order(self,method):
    for item in self.items:
        if item.so_detail:
            item.cost_center= frappe.db.get_value('Sales Order Item', item.so_detail, 'cost_center')   

def update_gst_hsn_code_cf_based_on_batch_no(self,method):
    for item in self.items:
        print('-'*10,'update_gst_hsn_code_cf_based_on_batch_no','item.batch_no',item.batch_no)
        if item.batch_no:
            item.gst_hsn_code=frappe.db.get_value('Batch',item.batch_no,'gst_hsn_code_cf')
            frappe.msgprint(_("HSN/SAC Code {0} is updated for <b> row {1} : Item {2}</b>").format(item.gst_hsn_code,item.idx,item.item_code),alert=1)

def set_sales_order_reference(self,method):
    if self.doctype=='Purchase Receipt':
        for item in self.items:
            if item.purchase_order and item.purchase_order_item:
                sales_order, sales_order_item = frappe.db.get_value('Purchase Order Item', item.purchase_order_item, ['sales_order', 'sales_order_item'])   
                frappe.db.set_value(item.doctype, item.name, {
                    'sales_order_cf': sales_order,
                    'sales_order_item_cf': sales_order_item
                })

    if self.doctype=='Batch': 
        if self.reference_doctype=='Purchase Receipt' and self.reference_name:
            pr_item_name=frappe.db.get_all('Purchase Receipt Item', filters={'item_code': ['=', self.item], 'batch_no': ['=', self.name],
                                                                            'parent':self.reference_name},pluck='name')
            if len(pr_item_name)>0:
                pr_item_name=pr_item_name[0]
                sales_order, sales_order_item = frappe.db.get_value('Purchase Receipt Item',pr_item_name, ['sales_order_cf', 'sales_order_item_cf'])
                frappe.db.set_value(self.doctype, self.name, {
                    'sales_order_cf': sales_order,
                    'sales_order_item_cf': sales_order_item
                })                

def update_batch_for_hsn_code(self,method):
    for item in self.items:
        print('-'*10,'update_batch_for_hsn_code','item.batch_no',item.batch_no)
        if item.batch_no:
            batch_no=frappe.get_doc('Batch',item.batch_no)
            batch_no.date_code_cf=item.date_code_cf
            batch_no.country_of_origin_cf=item.country_of_origin_cf
            batch_no.gst_hsn_code_cf=item.gst_hsn_code
            batch_no.save(ignore_permissions=True)
            frappe.msgprint(_("Batch no <b>{0}</b> is updated for <b> row {1} : Item {2}</b>").format(item.batch_no,item.idx,item.item_code),alert=1)

def update_batch_no_to_purchase_receipt(self,method):
    if self.gst_hsn_code_cf:
        pr_items=frappe.db.get_list('Purchase Receipt Item', filters={'batch_no': self.name},fields=['gst_hsn_code', 'name','item_code','parent'])
        for item in pr_items:
            if item.gst_hsn_code!=self.gst_hsn_code_cf:
                frappe.db.set_value('Purchase Receipt Item', item.name, 'gst_hsn_code', self.gst_hsn_code_cf)
                frappe.msgprint(_("Purchase Receipt <b>{0}</b> : Item {1}</b> : GST HSN Code is updated to {2}")
                 .format(item.parent,item.item_code,self.gst_hsn_code_cf),alert=1)

@frappe.whitelist(allow_guest=True)
def update_batch_no_of_existing_records():
    batch_list=frappe.db.get_list('Batch')
    for batch in batch_list:
        gst_hsn_code_cf = frappe.db.get_value('Batch', batch.name, 'gst_hsn_code_cf')
        if gst_hsn_code_cf:
            pr_items=frappe.db.get_list('Purchase Receipt Item', filters={'batch_no': batch.name},fields=['gst_hsn_code', 'name','item_code','parent','pr_detail'])
            print('batch',batch.name)
            for item in pr_items:
                if item.gst_hsn_code!=gst_hsn_code_cf:
                    frappe.db.set_value('Purchase Receipt Item', item.name, 'gst_hsn_code', gst_hsn_code_cf)
                    print("Purchase Receipt",item.parent,'item code',item.item_code,gst_hsn_code_cf)
                    if item.purchase_invoice_item:
                        frappe.db.set_value('Purchase Invoice Item', item.pr_detail, 'gst_hsn_code', gst_hsn_code_cf)
                        print("Purchase Invoice Item",item.pr_detail,'gst_hsn_code', gst_hsn_code_cf)
    frappe.db.commit()


