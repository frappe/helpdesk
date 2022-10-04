<template>
	<div>
		<Dialog
			:options="{ title: 'Add Agents' }"
			:show="show"
			@close="close()"
		>
			<template #body-content>
				<div class="space-y-3">
					<form
						@submit.prevent="onSubmit"
						class="flex flex-row space-x-2 items-center"
					>
						<Input
							id="searchInput"
							class="w-full"
							type="text"
							v-model="searchInput"
							placeholder="Type emails"
							@input="(val) => onSearchInputChange(val)"
						/>
						<Button
							appearance="primary"
							type="submit"
							v-if="currentInputIsValidEmail"
							icon="arrow-down"
							@click="
								() => {
									addToInviteQueue(searchInput)
									clearSearchInput()
								}
							"
						>
							Add
						</Button>
					</form>
					<div
						class="bg-gray-100 min-h-[100px] max-h-[300px] overflow-y-scroll px-2 rounded border flex flex-col"
					>
						<ul
							v-if="inviteQueue.length"
							class="flex flex-wrap gap-2 py-2"
						>
							<li
								class="flex items-center p-1 space-x-2 bg-white shadow rounded"
								v-for="email in inviteQueue.slice().reverse()"
								:key="email"
								:title="email"
							>
								<span class="text-base ml-2">
									{{ email }}
								</span>
								<button
									class="grid w-4 h-4 text-gray-700 rounded hover:bg-gray-300 place-items-center"
									@click="removeEmailFromQueue(email)"
								>
									<FeatherIcon class="w-3" name="x" />
								</button>
							</li>
						</ul>
					</div>
				</div>
			</template>
			<template #actions>
				<Button
					:disabled="inviteQueue.length == 0"
					appearance="primary"
					@click="sentInvites()"
					:loading="$resources.sentInvites.loading"
					>Sent Invites</Button
				>
				<Button appearance="secondary" @click="close()">Cancel</Button>
				<div class="grow">
					<Button
						@click="removeAllEmailFromQueue()"
						v-if="inviteQueue.length > 1"
					>
						Clear All
					</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Dialog, Input, FeatherIcon } from "frappe-ui"
import { ref } from "@vue/reactivity"

export default {
	name: "AddNewAgentsDialog",
	props: ["show"],
	components: {
		Dialog,
		Input,
		FeatherIcon,
	},
	setup() {
		const searchInput = ref("")
		const inviteQueue = ref([])

		const currentInputIsValidEmail = ref(false)

		return {
			searchInput,
			inviteQueue,
			currentInputIsValidEmail,
		}
	},
	methods: {
		testEmailRegex(val) {
			let emailRegex = /^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$/
			return emailRegex.test(val)
		},
		onSearchInputChange(val) {
			val = val.replaceAll(" ", "")

			if (val == "") {
				document.getElementById("searchInput").value = ""
				return
			}

			const valStr = val
			const inputs = val.split(",")

			let clearInputFlag = false
			this.currentInputIsValidEmail = false
			inputs.forEach((input) => {
				if (this.testEmailRegex(input)) {
					if (inputs.length > 1) {
						this.addToInviteQueue(input)
						clearInputFlag = true
					} else {
						if (valStr.includes(",")) {
							this.addToInviteQueue(input)
							clearInputFlag = true
						} else {
							this.currentInputIsValidEmail = true
						}
					}
				}
			})
			if (clearInputFlag) {
				this.clearSearchInput()
			}
		},
		addToInviteQueue(email) {
			this.inviteQueue = [...new Set([...this.inviteQueue, email])]
		},
		removeEmailFromQueue(email) {
			this.inviteQueue = this.inviteQueue.filter((item) => item !== email)
		},
		removeAllEmailFromQueue() {
			this.inviteQueue = []
		},
		clearSearchInput() {
			this.currentInputIsValidEmail = false
			this.searchInput = ""

			const input = document.getElementById("searchInput")
			input.value = ""
			input.focus()
		},
		close() {
			this.searchInput = ""
			this.inviteQueue = []
			this.$emit("close")
		},
		sentInvites() {
			this.$resources.sentInvites.submit({
				emails: this.inviteQueue,
			})
		},
	},
	resources: {
		sentInvites() {
			return {
				method: "frappedesk.api.agent.sent_invites",
				onSuccess: (res) => {
					this.currentInputIsValidEmail = false
					this.searchInput = ""
					this.inviteQueue = []

					this.$toast({
						title: "Invites Sent Successfully!",
						customIcon: "circle-check",
						appearance: "success",
					})

					this.close()
				},
				onError: (err) => {
					if (err.exc_type == "PaywallReachedError") {
						this.$toast({
							title: "Paywall Reached!",
							text: "You have reached the maximum number of agents you can add. Please upgrade your plan to add more agents.",
							customIcon: "circle-fail",
							appearance: "danger",
							fixed: true,
						})
					} else {
						this.$toast({
							title: "Error Sending Invites!",
							customIcon: "circle-fail",
							appearance: "danger",
						})
					}
				},
			}
		},
	},
}
</script>
