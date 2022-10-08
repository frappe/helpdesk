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
				class="ml-[25px] flex flex-row items-center space-x-[20px] font-normal text-base"
			>
				<div
					class="flex flex-row space-x-2"
					@pointerleave="
						() => {
							ratingHovered = 0
						}
					"
				>
					<div v-for="index in [1, 2, 3, 4, 5]" :key="index">
						<FeatherIcon
							name="star"
							class="w-5 h-5 stroke-gray-500"
							:class="`
								${
									(ratingHovered ||
										satisfactionRating ||
										ticket.satisfaction_rating) >=
									index * 0.2
										? 'fill-yellow-500'
										: 'fill-gray-200'
								} 
								${submitted ? 'cursor-default' : 'cursor-pointer'}
							`"
							@pointerenter="
								() => {
									if (!submitted) {
										ratingHovered = index * 0.2
									}
								}
							"
							@click="
								() => {
									if (!submitted) {
										satisfactionRating = index * 0.2
									}
								}
							"
						/>
					</div>
				</div>
				<div class="text-sm text-gray-600">{{ ratingToText }}</div>
			</div>
		</div>
		<div
			v-if="!submitted && satisfactionRating != 0"
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
							satisfaction_rating: this.satisfactionRating,
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
		const satisfactionRating = ref(0)
		const feedbackText = ref("")
		const submitted = ref(false)

		const ratingHovered = ref(0)

		return {
			ratingHovered,
			satisfactionRating,
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
	computed: {
		ratingToText() {
			const rating = this.submitted
				? this.ticket.satisfaction_rating
				: this.ratingHovered || this.satisfactionRating
			if (rating == 0) {
				return ""
			} else if (rating < 0.4) {
				return "Very Bad"
			} else if (rating < 0.6) {
				return "Bad"
			} else if (rating < 0.8) {
				return "Average"
			} else if (rating < 1) {
				return "Good"
			} else {
				return "Very Good"
			}
		},
	},
	mounted() {
		this.submitted = this.ticket.feedback_submitted
	},
}
</script>
