<template>
	<BaseBreadcrumbs
		:breadcrumbs="breadcrumbs"
		:interactable="interactable"
		@item-click="
			(breadcrumb, index) => {
				if (!interactable) return
				if (index < breadcrumbs.length - 1) {
					if (overrideInteraction != null) {
						overrideInteraction(
							{
								name: breadcrumb.name,
								docname: breadcrumb.label,
							},
							index === 0
						)
					} else {
						$router.push({
							path: `/${isDesk ? 'frappedesk' : 'support'}/kb${
								breadcrumb.name
									? `/categories/${breadcrumb.name}`
									: ''
							}`,
						})
					}
				}
			}
		"
	/>
</template>

<script>
import BaseBreadcrumbs from "@/components/global/BaseBreadcrumbs.vue"

export default {
	name: "Breadcrumbs",
	props: {
		isDesk: {
			type: Boolean,
			default: false,
		},
		isRoot: {
			type: Boolean,
			default: false,
		},
		docType: {
			type: String,
			default: "Category",
		},
		docName: {
			type: String,
			default: null,
		},
		interactable: {
			type: Boolean,
			default: true,
		},
		overrideInteraction: {
			type: Function,
			default: null,
		},
	},
	components: {
		BaseBreadcrumbs,
	},
	computed: {
		breadcrumbs() {
			const breadcrumbs = [{ name: "", label: "Home" }]
			if (this.isRoot) {
				return breadcrumbs
			}
			return [...breadcrumbs, ...(this.$resources.breadcrumbs.data || [])]
		},
	},
	resources: {
		breadcrumbs() {
			if (this.isRoot || (!this.docType && !this.docName)) {
				return
			}
			return {
				url: "frappedesk.api.kb.get_breadcrumbs",
				params: {
					docType: this.docType,
					docName: this.docName,
				},
				auto: true,
			}
		},
	},
	methods: {
		isBreadcrumbLast(index) {
			return index == this.breadcrumbs.length - 1
		},
	},
}
</script>
