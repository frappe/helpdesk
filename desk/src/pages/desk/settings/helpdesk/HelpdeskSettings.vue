<template>
    <div class="p-5 overflow-auto h-full">
        <div class="mb-[16px]">
            <div class="font-normal">Helpdesk Settings</div>
        </div>
        <div class="w-53 flex flex-row space-x-2">
            <Input label="Helpdesk Name" type="text" v-model="helpdeskName" class="text-gray-600 w-52" @input="checkHelpdeskNameChange" />
            <div class="mt-[22px]">
                <Button :disabled="!helpdeskNameChanged" appearance="primary" @click="updateHelpdeskName"> Save </Button>
            </div>
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
        const newHelpdeskName = ref('')
        const helpdeskNameChanged = ref(false)

        return {
            helpdeskName,
            newHelpdeskName,
            helpdeskNameChanged
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
                    this.helpdeskNameChanged = false
                }
            }
        }
    },
    methods: {
        checkHelpdeskNameChange: debounce(function(name) {
            this.helpdeskNameChanged = this.helpdeskName != name
            this.newHelpdeskName = name
        }, 500),
        updateHelpdeskName() {
            this.$resources.updateHelpdeskName.submit({name: this.newHelpdeskName})
        } 
    },
    activated() {
        this.$event.emit('set-selected-setting', 'Helpdesk Settings')
    }
}
</script>