<template>
	<div>
		<div
			:v-if="conversations"
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
				/>
			</div>
		</div>
	</div>
</template>

<script>
import ConversationCard from "./ConversationCard.vue"

export default {
	name: "Conversations",
	props: ["ticket", "scrollToBottom"],
	components: {
		ConversationCard
	},
	resources: {
		conversations() {
			return {
				method: 'helpdesk.api.ticket.get_conversations',
				params: {
					ticket_id: this.ticket.name
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
			if (data['doctype'] == 'Ticket' && data['name'] == this.ticket.name) {
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