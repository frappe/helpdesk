<template>
  <div>
		<CustomDialog :options="{title: 'Create New Ticket'}" v-model="show">
			<template #body-content>
				<div class="space-y-4">
					<Input label="Subject" type="text" v-model="subject" />
					<quill-editor 
						:ref="editor"
						v-model:content="descriptionContent" 
						contentType="html" 
						:options="editorOptions"
						style="min-height:150px; max-height:200px; overflow-y: auto;"
					/>
					<div class="flex float-right space-x-2">
						<Button appearance="primary" @click="createTicket()">Create</Button>
					</div>
				</div>
			</template>
		</CustomDialog>
  </div>
</template>

<script>
import { Input } from 'frappe-ui'
import CustomDialog from '../global/CustomDialog.vue'
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
			assignTo: "",
			priority: "",
			type: "",
			status: "",

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
		CustomDialog,
		Input,
		QuillEditor
	},
	methods: {
		createTicket() {
			this.$tickets().createTicket({
				subject: this.subject,
				description: this.descriptionContent
			})
			this.$emit('ticketCreated')
		}
	}
}
</script>

<style>

</style>