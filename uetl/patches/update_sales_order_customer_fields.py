import frappe

# This patch updates customer fields(account_manager_cf, customer_support_cf, reporting_manager_cf) in Sales Order


def execute():
    print(
        "Updating customer fields(account_manager_cf, customer_support_cf, reporting_manager_cf) in Sales Order"
    )
    frappe.db.sql(
        """
    update `tabSales Order` tso  
    inner join tabCustomer tc on tso.customer  = tc.name 
        set tso.account_manager_cf = tc.account_manager , 
        tso.customer_support_cf = tc.customer_support_cf , 
        tso.reporting_manager_cf = tc.reporting_manager_cf 
        """,
        # debug=True,
    )
