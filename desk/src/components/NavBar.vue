<template>
    <div class="flow-root py-5 pl-5 pr-10">
        <div class="float-left flex">
            <div class="text-6xl font-bold">
                FH
            </div>
            <div class="ml-2 pt-2">
                (use icon)
            </div>
        </div>
        <div class="float-right flex space-x-3">
            <div class="border-r-2 pr-2">
                <div>Notifications</div>
            </div>
            <Avatar label="John Doe" imageURL="https://picsum.photos/200" />
        </div>
    </div>
</template>
<script>
import { Avatar } from 'frappe-ui'

export default {
    name: 'NavBar',
    components: {
        Avatar
    }
}
</script>