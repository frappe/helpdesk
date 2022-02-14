<template>
  <div>
      <Card title="Contact details">
            <div v-if="contact">
                <hr class="mb-4">
                <div class="text-base space-y-2">
                    <div class="flex space-x-2">
                        <Avatar class="h-4 w-4" label="John Doe" :imageURL="contact.image" />
                        <span class="pt-1">{{ contact.first_name + ' ' + contact.last_name}}</span>
                    </div>
                    <div class="flex space-x-2">
                        <FeatherIcon class="w-6 h-6 mx-1" name="mail" />
                        <span class="text-slate-500">{{ contact.email_id }}</span>
                    </div>
                    <div class="flex space-x-2">
                        <FeatherIcon class="w-6 h-6 mx-1" name="phone" />
                        <span class="text-slate-500">{{ contact.phone }}</span>
                    </div>
                </div>
                <hr class="my-3">
                <div class="text-base space-y-3">
                    <span class="text-green-500">Open Tickets (2)</span>
                    <div class="space-y-1 text-slate-700">
                        <p class="text-slate-500">How to clear payment schedule?</p>
                        <p class="text-slate-500">How to bring Helpdesk to FC?</p>
                    </div>
                </div>
            </div>
        </Card>
  </div>
</template>

<script>
import { Card, Avatar, FeatherIcon } from 'frappe-ui'

export default {
    name: 'ContactCard',
    props: ['contact'],
    components: {
        Card,
        Avatar,
        FeatherIcon
    }
}
</script>