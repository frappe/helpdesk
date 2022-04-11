<template>
	<div v-if="ticket">
		<div class="flex">
			<div 
				class="sm:w-1/5 m-1 mt-2"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.5rem)' : null }"
			>
				<InfoPanel :ticketId="ticket.name" />
			</div>
			<div
				class="sm:w-3/5 pt-3 px-4"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 9rem)' : null }"
			>
				<div class="flex items-center pb-3 mt-3">
					<span class="text-4xl">
						{{ ticket.subject }}
					</span>
				</div>
				<div class="flex space-x-2 mb-2">
					<div class="" v-for="item in ['Conversations', 'Activities', 'All']" :key="item">
						<div class="cursor-pointer px-3 py-1 rounded text-base" :class="show == item ? 'bg-blue-50 text-blue-600' :'hover:bg-gray-100'" @click="() => {show = item}">{{ item }}</div>
					</div>
				</div>
				<div class="flex flex-col h-full space-y-2">
					<div class="overflow-auto grow">
						<ConversationAndActivities :show="show" :ticketId="ticket.name" :scrollToBottom="scrollConversationsToBottom"/>
					</div>
					<div v-if="show != 'Activities'" class="flex flex-col pr-3 pb-10 pt-3">
						<div class="flex" v-if="editing">
							<div v-if="user.agent">
								<Avatar :label="user.username" class="cursor-pointer" v-if="user" :imageURL="user.profile_image" size="md" />
							</div>
							<div class="grow ml-3">
								<div class="bg-gray-200 rounded-t-md p-2">
									<div class="flex flex-row-reverse">
										<FileUploader @success="(file) => attachments.push(file)">
											<template
												v-slot="{ progress, uploading, openFileSelector }"
											>
												<div class="flex space-x-2 items-center">
													<div class="flex space-x-2">
														<div v-for="file in attachments" :key="file.name">
															<div class="flex space-x-2 items-center text-base bg-white rounded-md px-3 py-1">
																<div class="inline-block">
																	{{ file.file_name }}
																</div>
																<div>
																	<FeatherIcon name="x" class="h-3 w-3 cursor-pointer hover:stroke-red-400 stroke-3" @click="() => {
																		attachments = attachments.filter(x => x.name != file.name)
																	}"/>
																</div>
															</div>
														</div>
													</div>
													<div>
														<Button icon-left="plus" appearance="primary" class="inline-block" @click="openFileSelector" :loading="uploading">
															{{ uploading ? `Uploading ${progress}%` : 'Attachment' }}
														</Button>
													</div>
												</div>
											</template>
										</FileUploader>
									</div>
								</div>
								<div v-if="editing">
									<quill-editor 
										:ref="editor"
										v-model:content="content" 
										contentType="html" 
										:options="editorOptions"
										style="min-height:150px; max-height:200px; overflow-y: auto;"
									/>
									<div class="mt-2 space-x-2">
										<Button 
											:loading="this.$resources.submitConversation.loading" 
											@click="this.submitConversation" 
											appearance="primary" 
											:disabled="!user.agent && !user.isAdmin"
										>
											Send
										</Button>
										<Button 
											appearance="secondary" 
											@click="cancelEditing()"
										>
											Cancel
										</Button>
									</div>
								</div>
							</div>
						</div>
						<div class="flex space-x-2" v-else>
							<Button appearance="primary" @click="startEditing()">Reply</Button>
						</div>
					</div>
				</div>
			</div>
			<div 
				class="sm:w-1/5 m-1 mt-2"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.5rem)' : null }"
			>
				<ActionPanel :ticketId="ticket.name" />
			</div>
		</div>
	</div>
</template>
<script>
import { Badge, Card, Dropdown, Avatar, FileUploader, FeatherIcon } from 'frappe-ui'
import ConversationAndActivities from '@/components/desk/ticket/ConversationAndActivities.vue';
import InfoPanel from '@/components/desk/ticket/InfoPanel.vue';
import ActionPanel from '@/components/desk/ticket/ActionPanel.vue';
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css';
import { inject, ref } from 'vue'

export default {
	name: 'Ticket',
	props: ['ticketId'],
	components: {
		Badge,
		Card,
		Dropdown,
		Avatar,
		FileUploader,
		FeatherIcon,
		ConversationAndActivities,
		InfoPanel,
		ActionPanel,
		QuillEditor
	},
	data() {
		return {
			editing: false,
			scrollConversationsToBottom: false,
			content: "",
			editorOptions: {
				modules: {
					toolbar: [
						['bold', 'italic', 'underline', 'strike'],        // toggled buttons
						['blockquote', 'code-block'],

						[{ 'header': 1 }, { 'header': 2 }],               // custom button values
						[{ 'list': 'ordered'}, { 'list': 'bullet' }],

						[{ 'header': [1, 2, 3, 4, 5, 6, false] }],

						[{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
						
						['image'],
						
						[{ 'align': [] }],

						['clean']                                         // remove formatting button
					]
				},
				placeholder: 'Compose your reply...',
				theme: 'snow',
				bounds: 7,
			}
		}
	},
	setup() {
		const editor = ref(null);
		const viewportWidth = inject('viewportWidth')
		const user = inject('user')
		const tickets = inject('tickets')
		const ticketController = inject('ticketController')
		const show = ref('Conversations') // Conversations, Activities, All
		const attachments = ref([])
		
		return { 
			editor,
			viewportWidth,
			user,
			tickets,
			ticketController,
			show,
			attachments
		}
	},
	resources: {
		submitConversation() {
			return {
				method: 'helpdesk.api.ticket.submit_conversation_via_agent',
				onSuccess: () => {
					var element = document.getElementsByClassName("ql-editor");
					element[0].innerHTML = "";
					this.attachments = []
				}
			}
		}
	},
	computed: {
		ticket() {
			return this.tickets[this.ticketId] || null
		}
	},
	methods: {
		startEditing() {
			this.editing = true
			this.delayedConversationScroll()
		},
		cancelEditing() {
			this.editing = false
		},
		delayedConversationScroll() {
			function delay(time) {
				return new Promise(resolve => setTimeout(resolve, time));
			}

			delay(400).then(() => this.scrollConversationsToBottom = true)
			delay(1000).then(() => this.scrollConversationsToBottom = false)
		},
		submitConversation() {
			this.$resources.submitConversation.submit({
				ticket_id: this.ticketId,
				message: this.content,
				attachments: this.attachments.map(x => x.name)
			})
		},
		getNextTicket() {

		},
		getPreviousTicket() {

		}
	},
}
</script>