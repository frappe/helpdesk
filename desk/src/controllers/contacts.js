import { createDocumentResource } from "frappe-ui"
import { computed } from "vue"

function createContactDocumentResource(contactId, vm) {
	return createDocumentResource(
		{
			doctype: "Contact",
			name: contactId,
			debounce: 300,
		},
		vm
	)
}

function get(options, vm) {
	const contactId = options?.contactId
	const fieldname = options?.fieldname

	let resource = createContactDocumentResource(contactId, vm)
	let value = computed(() => {
		if (!resource?.doc) {
			if (resource) {
				resource.get.fetch()
			}
			return null
		}
		return fieldname ? resource?.doc[fieldname] : resource?.doc
	})
	return value
}

function set(contactId, fieldname, value) {
	let resource = createContactDocumentResource(contactId)
	return resource.setValue.submit({ [fieldname]: value })
}

const contacts = {
	get,
	set,
}

export { contacts }
