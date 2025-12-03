import frappe
from frappe import _


def csv_to_columns(csv_str):
    '''
    cols = """
        Investor,investor,Link,Customer,250
        Status,status,,,135
        Investment Sum,investment_sum,Currency,,160
        My Commission,my_commission,Currency,,160
    """
    return csv_to_columns(cols)

    '''
    props = ["label", "fieldname", "fieldtype", "options", "width"]
    columns = [
        dict(zip(props, [x.strip() for x in col.split(",")]))
        for col in csv_str.split("\n")
        if col.strip()
    ]

    for d in columns:
        d["label"] = _(d["label"])
        if "/" in d["fieldtype"]:
            fieldtype, options = d["fieldtype"].split("/")
            d["fieldtype"] = fieldtype
            d["options"] = options

    return columns
