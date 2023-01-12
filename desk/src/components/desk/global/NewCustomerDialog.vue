<template>
	<div>
		<Dialog
			:options="{ title: 'Add New Customer', size: 'sm' }"
			v-model="open"
		>
			<template #body-content>
				<div class="space-y-4">
					<div class="space-y-1">
						<Input
							label="Customer Name"
							type="text"
							placeholder="Tesla Inc."
							v-model="customer"
						/>
					</div>
					<div class="space-y-1">
						<Input
							label="Domain"
							type="text"
							placeholder="eg: tesla.com, mycompany.com"
							v-model="domain"
						/>
					</div>
					<div class="flex float-right space-x-2">
						<Button
							appearance="primary"
							@click="
								() => {
									addCustomer()
									close()
									this.$router.go()
								}
							"
							class="mr-auto"
							>Add</Button
						>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Input, Dialog, ErrorMessage } from "frappe-ui"
import { computed, ref, inject } from "vue"
export default {
	name: "newCustomerDialog",
	props: {
		modelValue: {
			type: Boolean,
			required: true,
		},
	},
	setup(props, { emit }) {
		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit("update:modelValue", val)
				if (!val) {
					emit("close")
				}
			},
		})
		return {
			open,
		}
	},
	components: {
		Dialog,
		Input,
	},
	data() {
		return {
			customer: "",
			domain: "",
		}
	},
	methods: {
		addCustomer() {
			const inputParams = {
				customer_name: this.customer,
				domain: this.domain,
			}
			this.$resources.newCustomer.submit({
				doc: {
					doctype: "FD Customer",
					...inputParams,
				},
			})
		},
		close() {
			this.customer = ""
			this.domain = ""
			this.$emit("close")
		},
	},
	resources: {
		newCustomer() {
			return {
				method: "frappe.client.insert",
				onSuccess: (doc) => {
					this.$router.push(`/helpdesk/customers`)
				},
			}
		},
	},
}
</script>
