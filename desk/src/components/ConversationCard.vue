<template>
  <div class="flex">
        <div>
            <Avatar :label="userName" :imageURL="profilePicUrl" />
        </div>
        <div class="grow ml-3">
            <div class="flex justify-between">
                <div class="flex">
                    <span class="pt-1">{{ userName }}</span>
                </div>
                <span class="text-slate-500">{{ time }}</span>
            </div>
            <div class="mt-2">
                <div class="p-5 bg-slate-50 rounded-md">
                    <div v-html="message"></div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { Avatar } from 'frappe-ui'

export default {
    name: 'ConversationCard',
    props: ['userName', 'profilePicUrl', 'time', 'message'],
    components: {
        Avatar
    }
}
</script>

<style>

</style>