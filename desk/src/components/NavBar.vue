<template>
    <div class="flow-root pb-3 pt-4 pl-5 pr-10 border-b-2 mb-2">
        <div class="float-left flex">
            <div class="text-6xl font-bold">
                <CustomIcons name="helpdesk" width="40" height="40"/>
            </div>
        </div>
        <div class="float-right flex space-x-3">
            <div class="border-r-2 pr-2 pt-1">
                <FeatherIcon class="w-5 h-5" name="bell" />
            </div>
            <Avatar label="John Doe" imageURL="https://picsum.photos/200" />
        </div>
    </div>
</template>
<script>
import { Avatar, FeatherIcon } from 'frappe-ui'
import CustomIcons from './CustomIcons.vue'

export default {
    name: 'NavBar',
    components: {
        Avatar,
        FeatherIcon,
        CustomIcons
    }
}
</script>