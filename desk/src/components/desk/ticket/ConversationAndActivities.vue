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
								:userName="getUserName(item)" 
								:profilePicUrl="item.sender.image ? item.sender.image : ''" 
								:time="item.creation" 
								:message="item.content"
								:color="getConversationCardColor(getUserName(item))"
								:attachments="item.attachments"
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
import { ref } from 'vue'

export default {
	name: "Conversations",
	props: ["show", "ticketId", "scrollToBottom"],
	components: {
		ConversationCard,
		LoadingText,
		ActivityCard
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
			return this.$resources.conversations.data || null;
		},
		activities() {
			return this.$resources.activities.data || null;
		},
		items() {
			this.$nextTick(() => {
				this.autoScrollToBottom();
			})
			switch(this.show) {
				case 'Conversations':
					return this.conversations
				case 'Activities':
					return this.activities
				case 'All':
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
	updated() {
		this.userColors = {}
		this.lastColorIndex = -1
	},
	methods: {
		getUserName(item) {
			return (item.sender.first_name ? item.sender.first_name : '') + ' ' + (item.sender.last_name ? item.sender.last_name : '')
		},
		autoScrollToBottom() {
			if (this.items) {
				const [el] = this.$refs["item-" + (this.items.length - 1)];
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