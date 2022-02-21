<template>
    <div class="px-3" v-if="contact && ticket">
        <div class="py-4 border-b space-y-3">
            <div class="text-lg font-medium">Contact Information</div>
            <div class="text-base space-y-2">
                <div class="flex space-x-2">
                    <FeatherIcon name="user" class="w-4 h-4" />
                    <div class="text-slate-500 truncate">{{ contactFullName }}</div>
                </div>
                <div class="flex space-x-2">
                    <FeatherIcon name="mail" class="w-4 h-4" />
                    <span class="text-slate-500 truncate">{{ contact.email_id }}</span>
                </div>
                <div class="flex space-x-2">
                    <FeatherIcon name="phone" class="w-4 h-4" />
                    <span class="text-slate-500 truncate">{{ contact.phone }}</span>
                </div>
            </div>
        </div>
        <div class="py-4 border-b space-y-3" v-if="otherTicketsOfContact">
            <div class="text-lg font-medium">{{ `Open Tickets (${otherTicketsOfContact.length})` }}</div>
            <div class="space-y-1 " v-for="ticket in otherTicketsOfContact" :key="ticket.name">
                <router-link :to="`/tickets/${ticket.name}`" class="text-slate-500 text-base">
                    <div class="flex">
                        <FeatherIcon name="link" class="w-4 h-4"/>
                        <span class="text-slate-500 ml-2">{{ ticket.subject }}</span>
                    </div>
                </router-link>
            </div>
        </div>
        <div class="py-4">
            <div class="text-lg font-medium">Activity</div>
        </div>
    </div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'

export default {
	name: "InfoPanel",
    props: ["ticket", "contact"],
    components: {
        FeatherIcon
    },
    resources: {
        otherTicketsOfContact() {
			return {
				method: 'helpdesk.api.ticket.get_other_tickets_of_contact',
				params: {
					ticket_id: this.ticket.name,
				},
				auto: true
			}
		},
    },
    computed: {
        contactFullName() {
            if (this.contact) {
                return (this.contact.first_name || "") + " " + (this.contact.last_name || "")
            }
        },
        otherTicketsOfContact() {
			return this.$resources.otherTicketsOfContact.data || null;
		},
    }
}
</script>

<style>

</style>