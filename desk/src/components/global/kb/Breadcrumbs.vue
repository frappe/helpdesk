<template>
	<div class="flex flex-row space-x-2 items-center text-gray-600 text-base">
		<div v-for="(breadcrumb, index) in breadcrumbs" :key="breadcrumb">
			<div class="flex flex-row items-center space-x-2">
				<div
					@click="
						() => {
							if (!isBreadcrumbLast()) {
								$router.push({
									path: `/${
										[
											'DeskKBHome',
											'DeskKBCategory',
										].includes($route.name)
											? 'frappedesk'
											: 'support'
									}/kb${
										breadcrumb.name
											? `/categories/${breadcrumb.name}`
											: ''
									}`,
								})
							}
						}
					"
					:class="
						isBreadcrumbLast(index)
							? 'cursor-pointer hover:text-gray-900'
							: ''
					"
				>
					{{ breadcrumb.label }}
				</div>
				<div v-if="isBreadcrumbLast(index)">
					<FeatherIcon
						class="h-3 w-3 stroke-gray-500"
						name="chevron-right"
					/>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"

export default {
	name: "Breadcrumbs",
	props: {
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
	},
	components: {
		FeatherIcon,
	},
	computed: {
		breadcrumbs() {
			if (this.isRoot) {
				return []
			}
			return [
				{ name: "", label: "Home" },
				...(this.$resources.breadcrumbs.data || []),
			]
		},
	},
	resources: {
		breadcrumbs() {
			if (this.isRoot || (!this.docType && !this.docName)) {
				return
			}
			return {
				method: "frappedesk.api.kb.get_breadcrumbs",
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
			return index < this.breadcrumbs.length - 1
		},
	},
}
</script>
