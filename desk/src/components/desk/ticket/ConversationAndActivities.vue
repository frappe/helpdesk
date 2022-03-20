<template>
	<div>
		<div v-if="show === 'Conversations'">
			<div v-if="conversations">
				<div
					v-for="(conversation, index) in conversations" :key="conversation.name" 
					class="flex flex-col pr-3"
					ref="conversationContainer"
				>
					<div :ref="`conversation-${index}`">
						<ConversationCard 
							:userName="(conversation.sender.first_name ? conversation.sender.first_name : '') + ' ' + (conversation.sender.last_name ? conversation.sender.last_name : '')" 
							:profilePicUrl="conversation.sender.image ? conversation.sender.image : ''" 
							:time="conversation.creation" 
							:message="conversation.content"
							:isLast="index == conversations.length - 1"
						/>
					</div>
				</div>
			</div>
			<div v-else>
				<LoadingText />
			</div>
		</div>
		<div v-else-if="show === 'Activities'">
			Activities
		</div>
		<div v-else>
			Activities and Conversations
		</div>
	</div>
</template>

<script>
import ConversationCard from "./ConversationCard.vue"
import { LoadingText } from 'frappe-ui'

export default {
	name: "Conversations",
	props: ["show", "ticketId", "scrollToBottom"],
	components: {
		ConversationCard,
		LoadingText
	},
	resources: {
		conversations() {
			return {
				method: 'helpdesk.api.ticket.get_conversations',
				params: {
					ticket_id: this.ticketId
				},
				auto: true
			}
		},
	},
	computed: {
		conversations() {
			this.$nextTick(() => {
				this.autoScrollToBottom();
			})
			return this.$resources.conversations.data || null;
		}
	},
	watch: {
		scrollToBottom(scroll) {
			if (scroll) {
				this.autoScrollToBottom()
			}
		}
	},
	mounted() {
		this.$socket.on('list_update', (data) => {
			if (data['doctype'] == 'Ticket' && data['name'] == this.ticketId) {
				this.$resources.conversations.fetch()
			}
		});
	},
	unmounted() {
		this.$socket.off('list_update');
	},
	methods: {
		autoScrollToBottom() {
			if (this.conversations) {
				const [el] = this.$refs["conversation-" + (this.conversations.length - 1)];
				if (el) {
					el.scrollIntoView({behavior: 'smooth'});
				}
			}
		},
	}
}
</script>

<style>

</style>