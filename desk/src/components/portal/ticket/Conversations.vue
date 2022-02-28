<template>

</template>

<script>
import { inject } from '@vue/runtime-core'
export default {
    name: 'Conversation',
    props: ['ticketId'],
    setup() {
        const tickets = inject('tickets')
        const ticketController = inject('ticketController')

        return { tickets, ticketController }
    }
}
</script>

<style>

</style>