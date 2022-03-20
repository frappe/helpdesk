<template>
	<div>
		<div v-if="items">
			<div v-if="items.length > 0">
				<div 
					v-for="(item, index) in items" :key="item.name"
					ref="itemContainer"
				>	
					<div :ref="`item-${index}`">
						<div v-if="item.action">
							<ActivityCard 
								:action="item.action"
								:owner="item.owner"
								:creation="item.creation"
								:isLast="index == items.length - 1"
							/>
						</div>
						<div v-else-if="item.sender">
							<ConversationCard 
								:userName="(item.sender.first_name ? item.sender.first_name : '') + ' ' + (item.sender.last_name ? conversation.sender.last_name : '')" 
								:profilePicUrl="item.sender.image ? item.sender.image : ''" 
								:time="item.creation" 
								:message="item.content"
								:isLast="index == items.length - 1"
							/>
						</div>
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
import ActivityCard from "./ActivityCard.vue"
import { LoadingText } from 'frappe-ui'

export default {
	name: "Conversations",
	props: ["show", "ticketId", "scrollToBottom"],
	components: {
    ConversationCard,
    LoadingText,
    ActivityCard
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
		activities() {
			return {
				method: 'helpdesk.api.ticket.activities',
				params: {
					name: this.ticketId
				},
				auto: true
			}
		}
	},
	computed: {
		conversations() {
			this.$nextTick(() => {
				this.autoScrollToBottom();
			})
			return this.$resources.conversations.data || null;
		},
		activities() {
			this.$nextTick(() => {
				this.autoScrollToBottom();
			})
			return this.$resources.activities.data || null;
		},
		items() {
			switch(this.show) {
				case 'Conversations':
					console.log('conversation')
					return this.conversations
				case 'Activities':
					console.log('activities')
					return this.activities
				case 'All':
					console.log('all')
					let items = []
					items = this.activities ? [...items, ...this.activities]: items
					items = this.conversations ? [...items, ...this.conversations]: items
					items.sort((item1, item2) =>  new Date(item1.creation) - new Date(item2.creation))
					return items
			}
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
			if (data['doctype'] == 'Ticket Activity' && data['name'].split('-')[1] == this.ticketId) {
				this.$resources.activities.fetch()
			}
		});
	},
	unmounted() {
		this.$socket.off('list_update');
	},
	methods: {
		autoScrollToBottom() {
			if (this.items) {
				const [el] = this.$refs["item-" + (this.items.length - 1)];
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