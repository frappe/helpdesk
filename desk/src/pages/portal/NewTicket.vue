<template>
    <div v-if="template" class="mx-auto max-w-5xl pt-20">
        <div class="sm:w-8/12">
            <Card 
                :title="`New Ticket ${template.template_name != 'Default' ? `(${template.template_name})` : ''}`" class="space-y-6"
            >
                <div class="space-y-4 mb-4">
                    <div v-for="field in template.fields" :key="field">
                        <div v-if="field.fieldtype == 'Data'">
                            <Input :label="field.label" type="text" v-model="formData[field.fieldname]" />
                        </div>
                        <div v-else-if="field.fieldtype == 'Long Text'">
                            <Input :label="field.label" type="textarea" v-model="formData[field.fieldname]" />
                        </div>
                        <div v-else-if="field.fieldtype == 'Text Editor'">
                            <div class="block mb-2 text-sm leading-4 text-gray-700">{{ field.label }}</div>
                            <div>
                                <TextEditor showMenu="true" style="min-height:150px; max-height:200px; overflow-y: auto;" />
                            </div>
                        </div>
                    </div>
                </div>
                <div>
                    <Button appearance="primary">Submit</Button>
                </div>
                {{ formData }}
            </Card>
        </div>
    </div>
</template>
<script>
import { inject, ref } from 'vue'
import { Input, TextEditor, Card } from 'frappe-ui'

export default {
    name: 'NewTicket',
    props: ['templateId'],
    components: {
        Input,
        TextEditor,
        Card
    },
    setup() {
        const ticketTemplates = inject('ticketTemplates')
        const ticketController = inject('ticketController')

        const formData = ref({})

        return { ticketTemplates, ticketController, formData }
    },
    computed: {
        template() {
            const templateRoutes = this.ticketTemplates.map(x => x.template_route)
            if (templateRoutes.length > 0) {
                if (!templateRoutes.includes(this.templateId)) {
                    this.$router.push({ name: "DefaultNewTicket" })
                    return this.ticketTemplates.filter(x => x.template_route == 'default')[0]
                } else {
                    return this.ticketTemplates.filter(x => x.template_route == this.templateId)[0]
                }
            }
        }
    },
    resources: {
    },
    methods: {
        submitTicket() {
            if (validateTicketForm()) {
                this.ticketController.new('ticket', this.formData)
            }
        },
        validateTicketForm() {

        }
    }
}
</script>
<style>
</style>