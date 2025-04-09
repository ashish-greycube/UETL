import frappe
from frappe.utils.csvutils import build_csv_response
from uetl.uetl.report.sales_tracker_direct.sales_tracker_direct import execute
from frappe.desk.search import search_link
from frappe.utils.csvutils import send_csv_to_client


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


@frappe.whitelist(allow_guest=False)
def get_report_as_csv(**filters):
    # call api (/api/method/get_report_as_csv) with parameters in json body
    # e.g. { "report_name": "Sales Personwise Transaction UE", "company": "Unified Electro Tech Pvt Ltd", "customer": "Quadrant Future Tek Limited", "doc_type": "Sales Invoice", "from_date": "2023-04-01", "sales_person": "Yogesh Baghel", "territory": "East", "to_date": "2025-04-07" }

    def to_list(data, fieldnames):
        # return list of lists from list of dicts
        return [
            [d.get(f) or "" for f in fieldnames] for d in data if isinstance(d, dict)
        ]

    report_name = frappe.form_dict.report_name

    if not report_name:
        frappe.response.message = "Invalid or missing report name parameter"
    else:
        report = frappe.get_doc("Report", report_name)
        filters = frappe.form_dict or {}

        result = report.execute_script_report(filters)
        columns = result[0]
        data = result[1]
        # frappe.response["message"] = [columns , data]

        # make csv out of columns and data from report execute result
        fieldnames = [d.get("fieldname") for d in columns]
        csv = [[d.get("label") for d in columns]] + to_list(data, fieldnames)

        build_csv_response(data=csv, filename=report_name)


@frappe.whitelist(allow_guest=False)
def get_report_filter(field_name, report_name=None, party_type=None):
    """
    return filter values for fieldname to match desk report filters
    """

    frappe.set_user("Administrator")

    # commonly handle Link fields
    if frappe.db.exists("DocType", frappe.unscrub(field_name)):
        search_link(
            frappe.unscrub(field_name),
            txt="",
            ignore_user_permissions=True,
            page_length=1000,
        )
        return frappe.response.get("results")

    values = []

    # return 0 or 1 for check filters.
    check_values = [0, 1]

    if report_name == "Sales Personwise Transaction UE":
        values = {
            "doc_type": ["Sales Invoice", "Sales Order"],
            "show_return_entries": check_values,
        }.get(field_name)
    elif report_name == "Inventory Analysis UE":
        values = {
            "inventory_type": ["Sold", "Pending", "All"],
        }.get(field_name)
    elif report_name == "Accounts Receivable":
        if field_name == "party":
            values = frappe.db.get_link_options(party_type or "Customer", "")
        else:
            values = {
                "ageing_based_on": ["Posting Date", "Due Date"],
                "party_type": ["Customer", "Student"],
                "group_by_party": check_values,
                "based_on_payment_terms": check_values,
                "show_future_payments": check_values,
                "show_delivery_notes": check_values,
                "show_sales_person": check_values,
                "show_remarks": check_values,
                "for_revaluation_journals": check_values,
                "ignore_accounts": check_values,
                "in_party_currency": check_values,
            }.get(field_name)

    return values or []
