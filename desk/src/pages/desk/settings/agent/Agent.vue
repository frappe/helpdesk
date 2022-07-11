<template>
    <div class="flex flex-row w-full h-full">
        <AgentInfo class="shrink-0 border-r border-[#F4F5F6]" :agent="agentId" />
        <RelatedInfo class="grow" :agent="agentId" />
    </div>
</template>

<script>
import AgentInfo from '@/components/desk/settings/agents/AgentInfo.vue'
import RelatedInfo from '@/components/desk/settings/agents/RelatedInfo.vue'

export default {
    name: 'Agent',
    props: ['agentId'],
    components: {
        AgentInfo,
        RelatedInfo
    },
    setup() {

    },
    activated() {
		this.$event.emit('set-selected-setting', 'Agents')
    },

}
</script>