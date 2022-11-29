<template>
	<div v-if="active" class="absolute bottom-11 right-0 m-4">
		<div class="w-[20rem] rounded-lg border bg-white p-3 shadow-md">
			<div class="flex flex-col space-y-3">
				<div
					class="flex flex-col w-full bg-gray-50 rounded-lg p-4 space-y-2"
				>
					<div
						class="flex flex-col w-full items-center border-b py-4 space-y-2"
					>
						<Avatar size="lg" label="Contact Id" />
						<div>
							{{
								`${contact.first_name} ${
									contact.last_name ? contact.last_name : ""
								}`
							}}
						</div>
					</div>
					<div
						class="flex flex-row items-center justify-between w-full text-base"
					>
						<div>Reference Ticket</div>
						<Button icon="arrow-up-right" appearance="minimal" />
					</div>
				</div>
				<div
					class="flex flex-row bg-gray-100 rounded-lg justify-between items-center p-2"
				>
					<div class="text-base">Time: 1:27</div>
					<Button icon="phone-off" appearance="danger" />
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Avatar } from "frappe-ui"
import { createDocumentResource } from "frappe-ui"
import { ref, computed, inject } from "vue"

export default {
	name: "Dialer",
	props: {},
	components: {
		Avatar,
	},
	data() {
		return {
			active: false,
		}
	},
	setup(props, context) {
		const contactId = ref(null)
		const to = ref(null)

		const resource = ref(null)
		const createCallLogDocumentResource = (callLogId) => {
			console.log(callLogId)
			resource.value = createDocumentResource(
				{
					doctype: "Avaya Call Log",
					name: callLogId,
					debounce: 300,
					realtime: true,
				},
				context
			)
		}

		const callLogDoc = computed(() => {
			console.log("resource.value", resource.value)
			if (!resource.value?.doc) {
				if (resource.value) {
					resource.value.get.fetch()
				}
				return null
			}
			return resource.value.doc
		})

		const $contacts = inject("$contacts")
		const contact = computed(() => {
			if (!contactId.value) return
			return $contacts.get({ contactId: contactId.value }, context).value
		})

		return {
			contactId,
			to,
			callLogDoc,
			createCallLogDocumentResource,
			contact,
		}
	},
	mounted() {
		this.$event.on("dialer:make-call", (options) => {
			if (this.active) {
				// TODO: check if current call is active, is yes then show alert, else make call
				this.$toast({
					title: "Call already in progress",
					customIcon: "circle-fail",
					appearance: "danger",
				})
				return
			}

			this.active = true

			this.contactId = options.contactId
			this.to = options.to

			console.log("dialer:make-call", options)

			this.makeCall()
		})
	},
	unmounted() {
		this.$event.off("dialer:make-call")
	},
	methods: {
		makeCall() {
			this.$resources.makeCall.submit({
				contact_id: this.contactId,
				to: this.to,
			})
		},
	},
	resources: {
		makeCall() {
			return {
				method: "frappedesk.api.avaya.make_call",
				onSuccess: (callLogId) => {
					console.log("onSuccess", callLogId)
					this.createCallLogDocumentResource(callLogId)
				},
				onError: (err) => {
					console.log(err)
				},
			}
		},
	},
}
</script>
