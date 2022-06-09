import frappe

# This patch updates customer fields(account_manager_cf, customer_support_cf, reporting_manager_cf) in Sales Order


def execute():
    print(
        "Updating customer fields(account_manager_cf, customer_support_cf, reporting_manager_cf) in Sales Invoice"
    )
    frappe.db.sql(
        """
    update `tabSales Invoice` tsi  
    inner join tabCustomer tc on tsi.customer  = tc.name 
        set tsi.account_manager_cf = tc.account_manager , 
        tsi.customer_support_cf = tc.customer_support_cf , 
        tsi.reporting_manager_cf = tc.reporting_manager_cf 
        """,
        # debug=True,
    )
