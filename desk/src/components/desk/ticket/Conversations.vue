<template>
	<div>
		<div v-if="conversations">
			<div v-if="conversations.length > 0">
				<div
					v-for="(conversation, index) in conversations"
					:key="conversation.name"
					ref="conversationContainer"
				>
					<div :ref="`conversation-${index}`">
						<div
							v-if="conversation.type == 'Communication'"
							class="border-gray-100"
							:class="`
								${index != 0 && conversations[index - 1].type === 'Comment' ? 'border-t' : ''} 
								${index != conversations.length - 1 ? 'border-b' : ''}
							`"
						>
							<ConversationCard
								:userName="getUserName(conversation)"
								:profilePicUrl="
									conversation.sender.image
										? conversation.sender.image
										: conversation.sender.user_image
								"
								:time="conversation.creation"
								:message="conversation.content"
								:attachments="conversation.attachments"
							/>
						</div>
						<CommentCard v-else :comment="conversation" />
					</div>
				</div>
			</div>
			<div v-else class="text-slate-500 m-4 text-base">
				Nothing to show
			</div>
		</div>
		<div v-else>
			<LoadingText />
		</div>
	</div>
</template>

<script>
import ConversationCard from "./ConversationCard.vue"
import { LoadingText } from "frappe-ui"
import { ref } from "vue"
import CommentCard from "./CommentCard.vue"

export default {
	name: "Conversations",
	props: ["ticketId", "scrollToBottom", "autoScroll"],
	components: {
		ConversationCard,
		LoadingText,
		CommentCard,
	},
	setup() {
		const userColors = ref({})
		const lastColorIndex = ref(-1)

		return { userColors, lastColorIndex }
	},
	resources: {
		communications() {
			return {
				cache: ["Ticket", "Conversations", this.ticketId],
				method: "frappedesk.api.ticket.get_conversations",
				params: {
					ticket_id: this.ticketId,
				},
				auto: true,
			}
		},
		comments() {
			return {
				cache: ["Ticket", "Comments", this.ticketId],
				method: "frappe.client.get_list",
				params: {
					doctype: "Frappe Desk Comment",
					fields: ["*"],
					filters: {
						reference_ticket: this.ticketId,
					},
					order_by: "creation asc",
				},
				auto: true,
			}
		},
	},
	computed: {
		conversations() {
			this.$nextTick(() => {
				this.autoScrollToBottom()
			})
			const communications = this.communications.map((x) => {
				x.type = "Communication"
				return x
			})
			const comments = this.comments.map((x) => {
				x.type = "Comment"
				return x
			})
			const conversations =
				[...communications, ...comments].sort(
					(a, b) => new Date(a.creation) - new Date(b.creation)
				) || []
			return conversations
		},
		communications() {
			return this.$resources.communications.data || []
		},
		comments() {
			return this.$resources.comments.data || []
		},
	},
	watch: {
		scrollToBottom(scroll) {
			if (scroll) {
				this.autoScrollToBottom()
			}
		},
	},
	mounted() {
		this.$socket.on("list_update", (data) => {
			if (data["doctype"] === "Ticket" && data["name"] == this.ticketId) {
				this.$resources.communications.fetch()
			}
			if (
				data["doctype"] === "Frappe Desk Comment" &&
				data["name"].split("-")[1] === this.ticketId
			) {
				this.$resources.comments.fetch()
			}
		})
	},
	unmounted() {
		this.$socket.off("list_update")
	},
	updated() {
		this.userColors = {}
		this.lastColorIndex = -1
	},
	methods: {
		getUserName(conversation) {
			return (
				(conversation.sender.first_name
					? conversation.sender.first_name
					: "") +
				" " +
				(conversation.sender.last_name
					? conversation.sender.last_name
					: "")
			)
		},
		autoScrollToBottom() {
			if (this.conversations && this.conversations.length > 0) {
				const [el] =
					this.$refs[
						"conversation-" + (this.conversations.length - 1)
					]
				if (el) {
					el.scrollIntoView({ behavior: "smooth" })
				}
			}
		},
	},
}
</script>

<style></style>
