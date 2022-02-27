<template>
  <div>
		<Dialog :options="{title: 'Create New Ticket'}" v-model="open">
			<template #body-content>
				<div class="space-y-4">
					<Input label="Subject" type="text" v-model="subject" />
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
import { inject, ref, computed } from 'vue'

export default {
	name: 'NewTicketDialog',
	props: {
		modelValue: {
			type: Boolean,
			required: true,
		},
	},
	setup(props, { emit }) {
		const editor = ref(null);
		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit('update:modelValue', val)
				if (!val) {
					emit('close')
				}
			},
		})

		const ticketController = inject('ticketController')

		return { editor, open, ticketController }
	},
	data() {
		return {
			subject: "",
			description: "",

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
    Dialog,
},
	methods: {
		createTicket() {
			this.ticketController.new('ticket', {
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