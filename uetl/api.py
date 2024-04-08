import frappe
from frappe.utils.csvutils import build_csv_response
from uetl.uetl.report.sales_tracker_direct.sales_tracker_direct import execute
from frappe.desk.search import search_link


@frappe.whitelist(allow_guest=False)
def get_sales_tracker(**filters):
    """filters can include report standard filters
    e.g. customer, so_status, sales_person, cost_center, brand, upg, territory
    """

    filters = frappe._dict(filters)
    # filters["customer"] = "Larsen & Toubro Limited (Bangalore)"

    columns, data = execute(filters)
    fieldnames = [d.get("fieldname") for d in columns]
    csv = [[d.get("label") for d in columns]]
    for d in data:
        csv.append([d.get(f) for f in fieldnames])
    build_csv_response(csv, "sales_tracker")


@frappe.whitelist(allow_guest=False)
def get_sales_tracker_filter(field_name):
    """
    Sales Person, Cost Center: name , parent
    Customer: name, customer_name, customer_group, territory, mobile_no, primary_address,
    """
    frappe.set_user("Administrator")
    link_fields = [
        "sales_person",
        "cost_center",
        "customer",
        "brand",
        "territory",
    ]
    if field_name in (
        "on_order_np_qty",
        "reserved_order_qty",
        "reserved_physical_qty",
        "sold_qty",
    ):
        return ["> 0", "= 0"]
    elif field_name in ("so_status",):
        return ["Open", "Closed", "All"]
    elif field_name in ("mr_date",):
        return ["Yesterday", "Today"]
    elif field_name in link_fields:
        search_link(
            frappe.unscrub(field_name),
            txt="",
            ignore_user_permissions=True,
            page_length=1000,
        )
        return frappe.response.get("results")
