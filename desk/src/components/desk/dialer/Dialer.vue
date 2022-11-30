<template>
	<div v-if="show" class="absolute bottom-11 right-0 m-4">
		<div class="w-[20rem] rounded-lg border bg-white p-3 shadow-md">
			<div v-if="callLog" class="flex flex-col space-y-3">
				<div
					class="flex flex-col w-full items-center text-[12px] italic text-gray-500"
				>
					{{ `STATUS: ${callLog.status.toUpperCase()}` }}
				</div>
				<div
					class="flex flex-col w-full bg-gray-50 rounded-lg p-4 space-y-2"
				>
					<div
						v-if="contact"
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
					<div
						v-if="callLog.call_started_at"
						class="text-base italic text-gray-500"
					>
						{{ `ONGOING: ${callDuration}` }}
					</div>
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
			show: false,
		}
	},
	setup(props, context) {
		const callDuration = ref(null)
		const resource = ref(null)
		const createCallLogDocumentResource = (callLogId) => {
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

		const callLog = computed(() => {
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
			if (!callLog.value) return
			return $contacts.get(
				{ contactId: callLog.value.contact_ref },
				context
			).value
		})

		return {
			callDuration,
			callLog,
			contact,

			createCallLogDocumentResource,
		}
	},
	watch: {
		callLog(newVal) {
			if (newVal && newVal.call_started_at) {
				setInterval(() => {
					let nowTime = new Date(this.$dayjs())
					let startTime = new Date(
						this.$dayjs(newVal.call_started_at)
					)
					this.callDuration = this.$dayjs
						.duration(
							parseInt((nowTime - startTime) / 1000),
							"seconds"
						)
						.format("H:m:s")
				}, 1000)
			}
		},
	},
	mounted() {
		// TODO: check if any ongoing call is there for the current agent.
		this.$event.on("dialer:make-call", (options) => {
			if (this.show) {
				// TODO: check if current call is active, is yes then show alert, else make call
				this.$toast({
					title: "Call already in progress",
					customIcon: "circle-fail",
					appearance: "danger",
				})
				return
			}
			this.show = true
			this.makeCall(options)
		})
	},
	unmounted() {
		this.$event.off("dialer:make-call")
	},
	methods: {
		makeCall(options) {
			this.$resources.makeCall.submit({
				contact_id: options.contactId,
				to: options.to,
			})
		},
	},
	resources: {
		makeCall() {
			return {
				method: "frappedesk.api.avaya.make_call",
				onSuccess: (callLogId) => {
					this.createCallLogDocumentResource(callLogId)
				},
				onError: (err) => {
					this.$toast({
						title: "Something went wrong while making call",
						text: err,
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
	},
}
</script>
