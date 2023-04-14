<template>
	<div>
		<Dialog
			:options="{ title: '&nbsp;', size: '2xl' }"
			:show="show"
			@close="close()"
		>
			<template #body-content>
				<div
					class="border-b border-grey-400 w-full pl-2 pb-4 absolute left-0 top-0 px-4 py-3 sm:px-6 flex justify-between items-center"
				>
					<div class="">Canned Responses</div>
					<Button
						icon="x"
						class="bg-transparent w-2 h-2"
						@click="close()"
					/>
				</div>
				<div
					class="w-full border bg-[#EBEEF0] h-8 flex flex-row items-center space-x-3 mt-5 rounded mb-3"
				>
					<FeatherIcon
						name="search"
						class="h-4 w-4 stroke-gray-500 ml-[8px]"
					/>
					<Input
						v-model="search"
						id="searchInput"
						class="grow text-sm text-left text-black border-0 bg-[#EBEEF0] h-[31px] rounded-none pl-0"
						type="text"
						placeholder="Search for response"
						@input="getCannedResponses"
					/>
				</div>
				<div
					class="divide-y divide-slate-200 max-h-[256px] overflow-y-auto"
				>
					<div
						v-for="item in this.cannedResponses"
						class="relative py-3"
					>
						<CustomIcons
							name="add-new"
							class="h-7 w-7 rounded p-1 mb-4 absolute right-0"
							role="button"
							@click="
								() => {
									addMessage(item)
									emitMessage()
									close()
								}
							"
						/>
						<Accordion class="my-2">
							<template v-slot:title>
								<span class="font-medium text-lg">{{
									item.title
								}}</span>
							</template>
							<template v-slot:content>
								<div
									v-html="item.message"
									class="ProseMirror prose font-normal text-lg text-slate-500 ml-5 mt-4"
								></div>
							</template>
						</Accordion>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Dialog, FeatherIcon, Input, Button } from "frappe-ui"
import Accordion from "@/components/global/Accordion.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { ref, computed, provide } from "vue"
export default {
	name: "CannedResponsesDialog",
	props: ["show"],
	components: {
		Dialog,
		FeatherIcon,
		Accordion,
		CustomIcons,
	},
	setup() {
		const listManager = ref([])
		const tempMessage = ref("")
		provide("tempMessage", tempMessage)
		return {
			listManager,
			tempMessage,
		}
	},
	data() {
		return {
			cannedResponses: [],
		}
	},
	methods: {
		close() {
			this.$emit("close")
			this.$emit("messageVal", this.tempMessage)
		},
		emitMessage() {
			this.$emit("messageVal", this.tempMessage)
		},
		addMessage(item) {
			this.tempMessage = item.message
		},
		getCannedResponses(event) {
			let title = event
			this.$resources.list.fetch({
				title: title,
			})
		},
	},
	resources: {
		list() {
			return {
				url: "helpdesk.api.cannedResponse.get_canned_response",
				onSuccess(val) {
					this.cannedResponses = val
					return this.cannedResponses
				},
			}
		},
	},
	beforeMount() {
		this.getCannedResponses()
	},
}
</script>
