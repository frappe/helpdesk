<template>
	<div v-if="show" class="absolute bottom-11 right-0 m-4">
		<div class="w-[20rem] rounded-lg border bg-white p-3 shadow-md">
			<div v-if="callLog" class="flex flex-col space-y-3">
				<div
					class="flex flex-col w-full bg-gray-50 rounded-lg p-4 space-y-2"
				>
					<div
						v-if="contact"
						class="flex flex-col w-full items-center border-b py-4 space-y-2"
					>
						<Avatar size="lg" label="Contact Id" />
						<div class="flex flex-col space-y-0.5 items-center">
							<div>
								{{
									`${contact.first_name} ${
										contact.last_name
											? contact.last_name
											: ""
									}`
								}}
							</div>
							<div class="text-base text-gray-500">
								{{ callLog.to }}
							</div>
						</div>
					</div>
					<router-link
						:to="{
							path: `/frappedesk/tickets/${callLog.ticket_ref}`,
						}"
					>
						<div
							class="flex flex-row items-center justify-between w-full text-base text-gray-600 hover:text-gray-900"
							role="button"
						>
							<div>{{ `Ticket: #${callLog.ticket_ref}` }}</div>
							<FeatherIcon
								name="arrow-up-right"
								class="h-4 w-4"
							/>
						</div>
					</router-link>
					<router-link
						:to="{
							path: `/frappedesk/contacts/${callLog.contact_ref}`,
						}"
					>
						<div
							class="flex flex-row items-center justify-between w-full text-base text-gray-600 hover:text-gray-900"
							role="button"
						>
							<div>{{ `Contact: ${callLog.contact_ref}` }}</div>
							<FeatherIcon
								name="arrow-up-right"
								class="h-4 w-4"
							/>
						</div>
					</router-link>
				</div>
				<div
					class="flex flex-row bg-gray-100 rounded-lg justify-between items-center p-2"
				>
					<div class="text-base italic text-gray-700 font-semibold">
						{{
							`${callLog.status
								.replace("-", " ")
								.toUpperCase()} ${
								callLog.status == "in-progress" &&
								callLog.call_started_at
									? callDuration
									: ""
							}`
						}}
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Avatar, FeatherIcon } from "frappe-ui"
import { createDocumentResource } from "frappe-ui"
import { ref, computed, inject } from "vue"

export default {
	name: "Dialer",
	props: {},
	components: {
		Avatar,
		FeatherIcon,
	},
	data() {
		return {
			show: false,
		}
	},
	setup(context) {
		const user = inject("user")
		const callDuration = ref(null)
		const resource = ref(null)
		const $socket = inject("$socket")
		const createCallLogDocumentResource = (callLogId) => {
			resource.value = createDocumentResource(
				{
					doctype: "Avaya Call Log",
					name: callLogId,
					debounce: 300,
					realtime: true,
				},
				{ $socket }
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
			user,

			callDuration,
			callLog,
			contact,

			createCallLogDocumentResource,
			resource,
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
		// check if any ongoing call is there for the current agent. if yes, then fetch the call log
		if (this.user && this.user.agent) {
			this.$resources.getOngoingCall.fetch()
		}

		this.$socket.on("list_update", (data) => {
			if (this.callLog && this.callLog.ticket_ref) {
				if (
					data["doctype"] === "Avaya Call Log" &&
					data["name"].split("-")[1] === this.callLog.ticket_ref
				) {
					if (this.resource) {
						this.resource.get.fetch()
					}
				}
			}
		})
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
		this.$socket.off("list_update")
		this.$event.off("dialer:make-call")
	},
	methods: {
		makeCall(options) {
			this.$resources.makeCall.submit({
				ticket_id: options.ticketId,
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
		getOngoingCall() {
			return {
				method: "frappe.client.get_list",
				params: {
					doctype: "Avaya Call Log",
					filters: {
						agent_ref: this.user.agent.name,
						status: ["not in", ["completed", "failed"]],
					},
					fields: ["name"],
				},
				onSuccess: (res) => {
					if (res.length) {
						this.show = true
						this.createCallLogDocumentResource(res[0].name)
					}
				},
			}
		},
	},
}
</script>
