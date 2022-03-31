<template>
    <div class="flow-root py-3 pl-5 pr-8 border-b">
        <div class="float-left">
            <div class="flex items-center">
                <div class="font-bold text-2xl">Settings</div>
            </div>
        </div>
        <div class="float-right">
            <div class="flex space-x-3 items-center">
                <div v-for="action in actions" :key="action">
                    <Button :appearance="action.appearance" @click="action.onClick()" :icon-left="action.icon">{{ action.label }}</Button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ["selectedSetting"],
    computed: {
        actions() {
            switch(this.$route.name) {
                case 'Agents':
                    return [
                        {
                            label: 'Add Agent',
                            icon: 'plus',
                            appearance: 'primary',
                            onClick: () => {
                                // TODO: redirect to new agent page
                            }
                        }
                    ]
                case 'SlaPolicies':
                    return [
                        {
                            label: 'Add Policy',
                            icon: 'plus',
                            appearance: 'primary',
                            onClick: () => {
                                this.$router.push({
                                    name: 'NewSlaPolicy'
                                })
                            }
                        }
                    ]
                default:
                    return []
            }
        }
    }
}
</script>

<style>

</style>