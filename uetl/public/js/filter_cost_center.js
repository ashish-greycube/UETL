frappe.ui.form.on(cur_frm.doc.doctype, {
	setup: function (frm) {
        frm.set_query('cost_center', () => {
            return {
                filters: {
                    is_group: 0
                }
            }
        })
        frm.set_query('cost_center', 'items', () => {
            return {
                filters: {
                    is_group: 0
                }
            }
        })        
	}
})

