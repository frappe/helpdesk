<template>
  <div>
		<Dialog :options="{title: 'Create New Ticket'}" v-model="show">
			<template #body-content>
				<div class="space-y-4">
					<Input label="Subject" type="text" v-model="subject" />
					<div class="space-y-2">
						<div class="flex justify-between items-center">
							<div 
								class="block mt-3 text-sm leading-4 text-gray-700"
							>
								Raised By
							</div>
							<Button v-if="!createNewContact" appearance="secondary" @click="() => {createNewContact = true}">New Contact</Button>
							<Button v-else appearance="secondary" @click="() => {createNewContact = false}">Use Exsisting</Button>
						</div>
						<div v-if="!createNewContact">
							<Input class="grow" type="text" v-model="subject" />
						</div>
						<div v-else class="space-y-4">
							<Input class="grow" type="text" v-model="subject" placeholder="Full Name"/>
							<Input class="grow" type="text" v-model="subject" placeholder="Email Id"/>
						</div>
					</div>
					<div>
						<span 
							class="block mb-2 text-sm leading-4 text-gray-700"
						>
							Description
						</span>
						<quill-editor 
							:ref="editor"
							v-model:content="descriptionContent" 
							contentType="html" 
							:options="editorOptions"
							style="min-height:150px; max-height:200px; overflow-y: auto;"
						/>
					</div>
					<div class="flex float-right space-x-2">
						<Button appearance="primary" @click="createTicket()">Create</Button>
					</div>
				</div>
			</template>
		</Dialog>
  </div>
</template>

<script>
import { Input, Dialog } from 'frappe-ui'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css';
import { ref } from 'vue'

export default {
	name: 'NewTicketDialog',
	props: ['show'],
	setup() {
		const editor = ref(null);

		return { editor }
	},
	data() {
		return {
			subject: "",
			description: "",

			contactEmailId: "",
			contactFullName: "",
			
			createNewContact: false,

			descriptionContent: "",
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
	components: {
		Input,
		QuillEditor,
		Dialog
	},
	methods: {
		createTicket() {
			this.$tickets().createTicket({
				subject: this.subject,
				description: this.descriptionContent,
				contact: {
					is_new: this.createNewContact,
					email_id: this.contactEmailId,
					full_name: this.contactFullName
				}
			})
			this.$emit('ticketCreated')
		}
	}
}
</script>

<style>

</style>