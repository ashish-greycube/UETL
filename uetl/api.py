import frappe
from frappe.utils.csvutils import build_csv_response
from uetl.uetl.report.sales_tracker_direct.sales_tracker_direct import execute


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
