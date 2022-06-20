<template>
	<div>
		<div v-if="conversations">
			<div v-if="conversations.length > 0">
				<div 
					v-for="(conversation, index) in conversations" :key="conversation.name"
					ref="conversationContainer"
				>
					<div :ref="`conversation-${index}`">
						<ConversationCard 
							:userName="getUserName(conversation)" 
							:profilePicUrl="conversation.sender.image ? conversation.sender.image : conversation.sender.user_image" 
							:time="conversation.creation" 
							:message="conversation.content"
							:attachments="conversation.attachments"
							:isLast="index == conversation.length - 1"
						/>
					</div>
				</div>
			</div>
			<div v-else class="text-slate-500 m-4 text-base">Nothing to show</div>
		</div>
		<div v-else>
			<LoadingText />
		</div>
	</div>
</template>

<script>
import ConversationCard from "./ConversationCard.vue"
import { LoadingText } from 'frappe-ui'
import { ref } from 'vue'

export default {
	name: "Conversations",
	props: ["ticketId", "scrollToBottom", "autoScroll"],
	components: {
		ConversationCard,
		LoadingText,
	},
	setup() {
		const userColors = ref({})
		const lastColorIndex = ref(-1)

		return { userColors, lastColorIndex }
	},
	resources: {
		conversations() {
			return {
				cache: ['Ticket', 'Conversations', this.ticketId],
				method: 'frappedesk.api.ticket.get_conversations',
				params: {
					ticket_id: this.ticketId
				},
				auto: true
			}
		},
	},
	computed: {
		conversations() {
			if (this.autoScroll) {
				this.$nextTick(() => {
					this.autoScrollToBottom();
				})
			}
			return this.$resources.conversations.data || null;
		},
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
	updated() {
		this.userColors = {}
		this.lastColorIndex = -1
	},
	methods: {
		getUserName(conversation) {
			return (conversation.sender.first_name ? conversation.sender.first_name : '') + ' ' + (conversation.sender.last_name ? conversation.sender.last_name : '')
		},
		autoScrollToBottom() {
			if (this.conversations && this.conversations.length > 0) {
				const [el] = this.$refs["conversation-" + (this.conversations.length - 1)];
				if (el) {
					el.scrollIntoView({behavior: 'smooth'});
				}
			}
		}
	}
}
</script>

<style>

</style>