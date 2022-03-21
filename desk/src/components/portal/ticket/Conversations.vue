<template>
	<div>
		<div v-if="conversations">
			<div
				v-for="(conversation, index) in conversations" :key="conversation.name" 
				class="flex flex-col pr-3"
				ref="conversationContainer"
			>
				<div :ref="`conversation-${index}`">
					<ConversationCard 
						:userName="getUserName(conversation)" 
						:profilePicUrl="conversation.sender.image ? conversation.sender.image : ''" 
						:time="conversation.creation" 
						:message="conversation.content"
						:color="getConversationCardColor(getUserName(conversation))"
					/>
					<!-- TODO: dynamically set color based on user -->
				</div>
			</div>
		</div>
		<div v-else class="p-5">
			<LoadingText text="Fetching conversations..."/>
		</div>
	</div>
</template>

<script>
import ConversationCard from "./ConversationCard.vue"
import { LoadingText } from 'frappe-ui'
import { ref } from 'vue'

export default {
	name: "Conversations",
	props: ["ticketId", "scrollToBottom"],
	components: {
		ConversationCard,
		LoadingText
	},
	setup() {
		const userColors = ref({})
		const lastColorIndex = ref(-1)

		return { userColors, lastColorIndex }
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
	updated() {
		this.userColors = {}
		this.lastColorIndex = -1
	},
	methods: {
		getUserName(conversation) {
			return (conversation.sender.first_name ? conversation.sender.first_name : '') + ' ' + (conversation.sender.last_name ? conversation.sender.last_name : '')
		},
		autoScrollToBottom() {
			if (this.conversations) {
				const [el] = this.$refs["conversation-" + (this.conversations.length - 1)];
				if (el) {
					el.scrollIntoView({behavior: 'smooth'});
				}
			}
		},
		getConversationCardColor(userName) {
			let cardColors = ['blue', 'gray', 'green', 'red']
			
			if (this.userColors[userName] === undefined) {
				if (this.lastColorIndex == cardColors.length - 1) {
					this.lastColorIndex = 0
				} else {
					this.lastColorIndex++
				}
				this.userColors[userName] = cardColors[this.lastColorIndex]
			}
			return this.userColors[userName]
		}
	}
}
</script>

<style>

</style>