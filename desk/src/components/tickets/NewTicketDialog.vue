<template>
  <div>
		<Dialog :options="{title: 'Create New Ticket'}" v-model="show">
			<template #body-content>
				<div class="space-y-4">
					<Input label="Subject" type="text" v-model="subject" />
					<Input label="Description" type="textarea" v-model="description" />
					<div class="flex float-right space-x-2">
						<Button appearance="primary" @click="createTicket()">Create</Button>
					</div>
				</div>
			</template>
		</Dialog>
  </div>
</template>

<script>
import { Dialog, Input } from 'frappe-ui'

export default {
	name: 'NewTicketDialog',
	props: ['show'],
	data() {
		return {
			subject: "",
			description: "",
			assignTo: "",
			priority: "",
			type: "",
			status: "",
		}
	},
	components: {
		Dialog,
		Input
	},
	methods: {
		createTicket() {
			this.$tickets().createTicket({
				subject: this.subject,
				description: this.description
			})
			this.$emit('ticketCreated')
		}
	}
}
</script>

<style>

</style>