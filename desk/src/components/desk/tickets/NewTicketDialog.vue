<template>
  <div>
		<Dialog :options="{title: 'Create New Ticket'}" v-model="open">
			<template #body-content>
				<div class="space-y-4">
					<div class="w-full">
						<span 
							class="block mb-2 text-sm leading-4 text-gray-700"
						>
							Raised By
						</span>
						<Combobox v-model="selectedContact">
							<ComboboxInput 
								class="rounded-md w-full py-1 border-none focus:ring-0 pl-3 pr-10 text-sm leading-5 text-gray-900 bg-gray-100"
								autocomplete="off"
								@change="query = $event.target.value" 
							/>
							<ComboboxOptions
								class="absolute z-50 mt-1 overflow-auto text-base bg-white rounded-md shadow-lg max-h-40 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
							>
								<div
									v-if="filterdContacts.length === 0 && query !== ''"
									class="select-none py-2 relative px-4 text-gray-700 cursor-pointer"
									@click="() => {showNewContactDialog = true}"
								>
									Create new
								</div>
								<ComboboxOption
									v-slot="{ selected, active }"
									v-for="contactItem in filterdContacts" :key="contactItem"
									:value="contactItem.name"
								>
									<li
										class="cursor-default select-none relative py-2 pl-4 pr-4 text-gray-900"
										:class="{'bg-slate-50': active}"
									>
										<span
											class="block truncate"
											:class="{ 'font-medium': selected, 'font-normal': !selected }"
											>
											{{ contactItem.name }}
										</span>
									</li>
								</ComboboxOption>
							</ComboboxOptions>
						</Combobox>
					</div>
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
						<Button 
							appearance="primary" 
							@click="createTicket()" 
							:loading="isCreating"
						>
							Create
						</Button>
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
import {
	Combobox,
	ComboboxInput,
	ComboboxOptions,
	ComboboxOption,
} from '@headlessui/vue'

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
		const isCreating = ref(false);

		const contactName = ref('')
		const selectedContact = ref('')
		const query = ref('')

		const contacts = inject('contacts')

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

		return { editor, isCreating, contactName, selectedContact, query, contacts, open, ticketController }
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
	computed: {
		filterdContacts() {
			return this.query === ''
				? this.contacts
				: this.contacts.filter((contactItem) => {
					return contactItem.name.toLowerCase().includes(this.query.toLowerCase())
				})
		}
	},
	components: {
		Input,
		QuillEditor,
		Dialog,
		Combobox,
		ComboboxInput,
		ComboboxOption,
		ComboboxOptions,
	},
	methods: {
		createTicket() {
			// TODO: do validation
			this.isCreating = true
			this.ticketController.new('ticket', {
				contact: this.selectedContact,
				subject: this.subject,
				description: this.descriptionContent
			}).then(() => {
				this.isCreating = false
				this.$emit('ticketCreated')
			})
		}
	}
}
</script>

<style>

</style>