from . import __version__ as app_version

app_name = "uetl"
app_title = "UETL"
app_publisher = "GreyCube Technologies"
app_description = "Customization for Univa Tech"
app_icon = "octicon octicon-plug"
app_color = "yellow"
app_email = "admin@greycube.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/uetl/css/uetl.css"
# app_include_js = "/assets/uetl/js/uetl.js"

# include js, css files in header of web template
# web_include_css = "/assets/uetl/css/uetl.css"
# web_include_js = "/assets/uetl/js/uetl.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "uetl/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Sales Order" : "public/js/filter_cost_center.js",	
	}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "uetl.install.before_install"
# after_install = "uetl.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "uetl.uninstall.before_uninstall"
# after_uninstall = "uetl.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "uetl.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
	"Sales Order": {
		"validate": "uetl.doc_events.validate_for_duplicate_items_based_on_date"
	},
	"Purchase Order": {
		"validate": ["uetl.doc_events.validate_for_duplicate_items_based_on_date",
		"uetl.doc_events.validate_so_reference_in_item"	]		
	},
	"Delivery Note": {
		"validate": ["uetl.doc_events.set_cost_center_based_on_sales_order",
		"uetl.doc_events.update_gst_hsn_code_cf_based_on_batch_no"
		]
	},
	"Purchase Receipt": {
		"after_insert":"uetl.doc_events.set_sales_order_reference",
		"on_submit":"uetl.doc_events.update_batch_for_hsn_code"
	},
	"Batch": {
		"after_insert":"uetl.doc_events.set_sales_order_reference",
		"on_update":"uetl.doc_events.update_batch_no_to_purchase_receipt"
	}				
}
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"uetl.tasks.all"
# 	],
# 	"daily": [
# 		"uetl.tasks.daily"
# 	],
# 	"hourly": [
# 		"uetl.tasks.hourly"
# 	],
# 	"weekly": [
# 		"uetl.tasks.weekly"
# 	]
# 	"monthly": [
# 		"uetl.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "uetl.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "uetl.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "uetl.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"uetl.auth.validate"
# ]

