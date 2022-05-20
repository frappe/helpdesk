<template>
	<div class="p-[10px] rounded-[6px]" :class="submitted ? 'bg-gray-50' : 'bg-white shadow-lg border-blue-500 border-2'">
		<div class="text-[14px] font-medium pb-[8px]">{{ submitted ? 'This ticket was rated as:' : 'How did we do?' }}</div>
		<div v-if="!submitted" class="flex flex-col space-y-[8px]">
			<div class="flex flex-row items-center space-x-[8px] font-normal text-[12px]">
				<div class="flex flex-row items-center space-x-[8px]">
					<Input type="checkbox" :checked="satisfaction === 'Satisfied'" @click="() => { satisfaction = (satisfaction != 'Satisfied') ? 'Satisfied' : 'Not Set' }" />
					<span>Good, I’m satisfied.</span>
				</div>
				<div class="flex flex-row items-center space-x-[8px]">
					<Input type="checkbox" :checked="satisfaction === 'Un Satisfied'" @click="() => { satisfaction = (satisfaction != 'Un Satisfied') ? 'Un Satisfied' : 'Not Set' }" />
					<span>Bad, I’m not satisfied.</span>
				</div>
			</div>
			<Input v-if="satisfaction != 'Not Set'" type="textarea" :value="feedbackText" @input="(newValue) => { feedbackText = newValue }" placeholder="Tell us about your experience." />
			<div>
				<Button 
					v-if="feedbackText != '' && satisfaction != 'Not Set'" 
					appearance="primary" 
					:loading="$resources.submitFeedback.loading"
					@click="$resources.submitFeedback.submit({
						ticket_id: ticket.name,
						satisfied: (this.satisfaction === 'Satisfied'),
						feedback_text: (this.feedbackText)
					})"
				> 
					Submit my review
				</Button>
			</div>
		</div>
		<div v-else class="flex flex-col space-y-[8px] text-[12px] font-normal">
			<div>{{ ticket.satisfied ? 'Good, I’m satisfied.' : 'Bad, I’m not satisfied.' }}</div>
			<div class="flex flex-col space-y-[2px]">
				<div>Review:</div>
				<div>‘{{ ticket.customer_feedback }}’</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ref } from '@vue/reactivity'
import { Input } from 'frappe-ui'

export default {
	name: 'CustomerSatiscationFeedback',
	props: ['ticket'],
	components: {
		Input
	},
	setup() {
		const satisfaction = ref('Not Set')
		const feedbackText = ref('')
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
				method: 'frappedesk.api.ticket.submit_customer_feedback',
				onSuccess() {
					this.submitted = true
				}
			}
		}
	},
	mounted() {
		console.log(this.ticket)
		this.submitted = this.ticket.feedback_submitted
	},
}
</script>

<style>

</style>