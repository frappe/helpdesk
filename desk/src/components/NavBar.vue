<template>
    <div class="flow-root pb-3 pt-4 pl-5 pr-8 border-b">
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