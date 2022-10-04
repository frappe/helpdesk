<template>
	<div
		class="p-[10px] rounded-[6px] text-gray-900 bg-white shadow-sm border flex flex-col space-y-[8px]"
	>
		<div class="flex flex-row items-center">
			<div class="text-[14px] font-medium">
				{{
					submitted
						? fromDesk
							? "Rating"
							: "You Rated"
						: "How did we do?"
				}}
			</div>
			<div
				v-if="!submitted"
				class="ml-[80px] flex flex-row items-center space-x-[40px] font-normal text-base"
			>
				<div
					class="flex flex-row items-center space-x-[8px] cursor-pointer"
					@click="
						() => {
							satisfaction =
								satisfaction != 'Satisfied'
									? 'Satisfied'
									: 'Not Set'
						}
					"
				>
					<FeatherIcon
						name="smile"
						class="w-[14px] h-[14px]"
						:class="
							satisfaction === 'Satisfied'
								? 'stroke-blue-500'
								: 'stroke-gray-400'
						"
					/>
					<span>Good, I’m satisfied.</span>
				</div>
				<div
					class="flex flex-row items-center space-x-[8px] cursor-pointer"
					@click="
						() => {
							satisfaction =
								satisfaction != 'Un Satisfied'
									? 'Un Satisfied'
									: 'Not Set'
						}
					"
				>
					<FeatherIcon
						name="frown"
						class="w-[14px] h-[14px]"
						:class="
							satisfaction === 'Un Satisfied'
								? 'stroke-red-500'
								: 'stroke-gray-400'
						"
					/>
					<span>Bad, I’m not satisfied.</span>
				</div>
			</div>
			<div
				v-else
				class="ml-[10px] flex flex-row items-center space-x-[6px] text-base"
			>
				<FeatherIcon
					:name="ticket.satisfied ? 'smile' : 'frown'"
					class="w-[14px] h-[14px]"
					:class="
						ticket.satisfied ? 'stroke-blue-500' : 'stroke-red-400'
					"
				/>
				<div>
					{{
						ticket.satisfied
							? "Good, I’m satisfied."
							: "Bad, I’m not satisfied."
					}}
				</div>
			</div>
		</div>
		<div
			v-if="!submitted && satisfaction != 'Not Set'"
			class="flex flex-col space-y-[8px]"
		>
			<Input
				type="textarea"
				class="focus:bg-white bg-white border border-gray-200 rounded focus:border-gray-400"
				:value="feedbackText"
				@input="
					(newValue) => {
						feedbackText = newValue
					}
				"
				placeholder="Tell us about your experience."
			/>
			<div>
				<Button
					appearance="primary"
					:loading="$resources.submitFeedback.loading"
					@click="
						$resources.submitFeedback.submit({
							ticket_id: ticket.name,
							satisfied: this.satisfaction === 'Satisfied',
							feedback_text: this.feedbackText,
						})
					"
				>
					Submit my review
				</Button>
			</div>
		</div>
		<div
			v-if="submitted && (ticket.customer_feedback || feedbackText)"
			class="flex flex-col space-y-[8px] text-[12px] font-normal text-gray-700"
		>
			<div class="flex flex-col space-y-[2px]">
				<div class="italic">
					"{{ ticket.customer_feedback || feedbackText }}"
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ref } from "@vue/reactivity"
import { Input, FeatherIcon } from "frappe-ui"

export default {
	name: "CustomerSatiscationFeedback",
	props: ["ticket", "editable", "fromDesk"],
	components: {
		Input,
		FeatherIcon,
	},
	setup() {
		const satisfaction = ref("Not Set")
		const feedbackText = ref("")
		const submitted = ref(false)

		return {
			satisfaction,
			feedbackText,
			submitted,
		}
	},
	resources: {
		submitFeedback() {
			return {
				method: "frappedesk.api.ticket.submit_customer_feedback",
				onSuccess() {
					this.submitted = true
				},
			}
		},
	},
	mounted() {
		this.submitted = this.ticket.feedback_submitted
	},
}
</script>

<style></style>
