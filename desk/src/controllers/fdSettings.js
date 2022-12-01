import { createDocumentResource } from "frappe-ui"
import { computed } from "vue"

function get(options, vm) {
	const fieldname = options?.fieldname

	let resource = createDocumentResource(
		{
			doctype: "Frappe Desk Settings",
			name: "Frappe Desk Settings",
			debounce: 300,
			realtime: true,
		},
		vm
	)

	let value = computed(() => {
		if (!resource?.doc) {
			if (resource) {
				resource.get.fetch()
			}
			return null
		}
		return fieldname ? resource.doc[fieldname] : resource.doc
	})
	return value
}

const fdSettings = {
	get,
}

export { fdSettings }
