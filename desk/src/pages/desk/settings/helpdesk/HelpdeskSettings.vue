<template>
    <div class="p-5 overflow-auto h-full">
        <div class="mb-[16px]">
            <div class="font-semibold">Helpdesk Settings</div>
        </div>
        <div class="w-53">
            <Input label="Helpdesk Name" type="text" v-model="helpdeskName" class="text-gray-600 w-52" @input="updateHelpdeskName" />
        </div>
    </div>
</template>

<script>
import { ref } from '@vue/reactivity'
import { Input, debounce } from 'frappe-ui'

export default {
    name: 'HelpdeskSettings',
    components: {
        Input
    },
    setup() {
        const helpdeskName = ref('')

        return {
            helpdeskName
        }
    },
    resources: {
        helpdeskName() {
			return {
				method: 'frappedesk.api.website.helpdesk_name',
				auto: true,
				onSuccess: (res) => {
					this.helpdeskName = res
				}
			}
		},
        updateHelpdeskName() {
            return {
                method: 'frappedesk.api.settings.update_helpdesk_name',
                onSuccess: (res) => {
                    document.title = `FrappeDesk ${res ? ` | ${res}` : ''}`
                    this.helpdeskName = res
                    this.$toast({
                        title: 'Helpdesk name updated!!',
                        customIcon: 'circle-check',
                        appearance: 'success',
                    })
                }
            }
        }
    },
    methods: {
        updateHelpdeskName: debounce(function(name) {
            this.$resources.updateHelpdeskName.submit({name})
        }, 500)
    }
}
</script>