import { createDocumentResource } from "frappe-ui"
import { computed } from "vue"

function createAgentDocumentResource(agentId, vm) {
	return createDocumentResource(
		{
			doctype: "Agent",
			name: agentId,
			debounce: 300,
		},
		vm
	)
}

function get(options, vm) {
	const agentId = options?.agentId
	const fieldname = options?.fieldname

	let resource = createAgentDocumentResource(agentId, vm)
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

function set(agentId, fieldname, value) {
	let resource = createAgentDocumentResource(agentId)
	return resource.setValue.submit({ [fieldname]: value })
}

const agents = {
	get,
	set,
}

export { agents }
