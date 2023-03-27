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
								:user-name="getUserName(conversation)"
								:profile-pic-url="
									conversation.sender.image
										? conversation.sender.image
										: conversation.sender.user_image
								"
								:time="conversation.creation"
								:message="conversation.content"
								:attachments="conversation.attachments"
								:cc="conversation.cc"
								:bcc="conversation.bcc"
							/>
						</div>
						<CommentCard v-else :comment="conversation" />
					</div>
				</div>
			</div>
			<div v-else class="m-4 text-base text-slate-500">Nothing to show</div>
		</div>
		<div v-else>
			<LoadingText />
		</div>
	</div>
</template>

<script>
import { ref } from "vue";
import { LoadingText } from "frappe-ui";
import CommentCard from "./CommentCard.vue";
import ConversationCard from "./ConversationCard.vue";

export default {
	name: "Conversations",
	components: {
		ConversationCard,
		LoadingText,
		CommentCard,
	},
	props: ["ticketId", "scrollToBottom", "autoScroll"],
	setup() {
		const userColors = ref({});
		const lastColorIndex = ref(-1);

		return { userColors, lastColorIndex };
	},
	resources: {
		communications() {
			return {
				cache: ["HD Ticket", "Conversations", this.ticketId],
				url: "helpdesk.api.ticket.get_conversations",
				params: {
					ticket_id: this.ticketId,
				},
				auto: true,
			};
		},
		comments() {
			return {
				cache: ["HD Ticket", "Comments", this.ticketId],
				url: "frappedesk.extends.client.get_list",
				params: {
					doctype: "HD Ticket Comment",
					fields: ["*"],
					filters: {
						reference_ticket: this.ticketId,
					},
					order_by: "creation asc",
				},
				auto: true,
			};
		},
	},
	computed: {
		conversations() {
			this.$nextTick(() => {
				this.autoScrollToBottom();
			});
			const communications = this.communications.map((x) => {
				x.type = "Communication";
				return x;
			});
			const comments = this.comments.map((x) => {
				x.type = "Comment";
				return x;
			});
			const conversations =
				[...communications, ...comments].sort(
					(a, b) => new Date(a.creation) - new Date(b.creation)
				) || [];
			return conversations;
		},
		communications() {
			return this.$resources.communications.data || [];
		},
		comments() {
			return this.$resources.comments.data || [];
		},
	},
	watch: {
		scrollToBottom(scroll) {
			if (scroll) {
				this.autoScrollToBottom();
			}
		},
	},
	mounted() {
		this.$socket.on("new_frappedesk_communication", (data) => {
			if (data.ticket_id != this.ticketId) return;

			this.$resources.communications.reload();
		});

		this.$socket.on("new_frappedesk_comment", (data) => {
			if (data.ticket_id != this.ticketId) return;

			this.$resources.comments.reload();
		});
	},
	unmounted() {
		this.$socket.off("new_frappedesk_communication");
		this.$socket.off("new_frappedesk_comment");
	},
	updated() {
		this.userColors = {};
		this.lastColorIndex = -1;
	},
	methods: {
		getUserName(conversation) {
			return (
				(conversation.sender.first_name ? conversation.sender.first_name : "") +
				" " +
				(conversation.sender.last_name ? conversation.sender.last_name : "")
			);
		},
		autoScrollToBottom() {
			if (this.conversations && this.conversations.length > 0) {
				const [el] =
					this.$refs["conversation-" + (this.conversations.length - 1)];
				if (el) {
					el.scrollIntoView({ behavior: "smooth" });
				}
			}
		},
	},
};
</script>
