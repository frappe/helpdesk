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
		<NewAgentDialog v-model="showNewAgentDialog" @agent-created="() => {
				showNewAgentDialog = false
				$router.go()
			}" 
		/>
	</div>
</template>

<script>
import { ref } from '@vue/reactivity';
import NewAgentDialog from "../global/NewAgentDialog.vue"
export default {
    props: ["selectedSetting"],
	setup() {
		const showNewAgentDialog = ref(false)
		
		return { showNewAgentDialog }
	},
    computed: {
        actions() {
            switch (this.$route.name) {
                case "Agents":
                    return [
                        {
                            label: "Add Agent",
                            icon: "plus",
                            appearance: "primary",
                            onClick: () => {
								this.showNewAgentDialog = true
                            }
                        }
                    ];
                case "SlaPolicies":
                    return [
                        {
                            label: "Add Policy",
                            icon: "plus",
                            appearance: "primary",
                            onClick: () => {
                                this.$router.push({
                                    name: "NewSlaPolicy"
                                });
                            }
                        }
                    ];
                default:
                    return [];
            }
        }
    },
    components: { NewAgentDialog }
}
</script>

<style>

</style>