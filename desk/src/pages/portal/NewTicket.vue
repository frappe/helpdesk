<template>
    <div>
        New Ticket ({{template}})
    </div>
</template>
<script>
import { inject } from '@vue/runtime-core'

export default {
    name: 'NewTicket',
    props: ['templateId'],
    components: {
    },
    setup() {
        const ticketTemplates = inject('ticketTemplates')
        const ticketController = inject('ticketController')

        return { ticketTemplates, ticketController }
    },
    computed: {
        template() {
            const templateRoutes = this.ticketTemplates.map(x => x.template_route)
            if (templateRoutes.length > 0) {
                if (!templateRoutes.includes(this.templateId)) {
                    this.$router.push({ name: "DefaultNewTicket" })
                    return 'default'
                } else {
                    return this.templateId
                }
            }
        }
    },
    resources: {
    },
    methods: {
    }
}
</script>
<style>
</style>