<template>
    <Switch
        v-model="modelValue"
        :class="modelValue ? 'border-blue-500' : 'border-gray-700'"
        class="relative inline-flex items-center h-4 bg-white border rounded-full w-[1.7rem]"
    >
        <span
            :class="modelValue ? 'translate-x-[0.9rem] bg-blue-500' : 'translate-x-1 bg-gray-700'"
            class="inline-block w-[0.5rem] h-[0.5rem] transform rounded-full"
        />
    </Switch>
</template>

<script>
import { Switch } from '@headlessui/vue'

export default {
    name: "CustomSwitch",
    components: {
        Switch
    },
    props: ['modelValue'],
    watch: {
        modelValue(newValue) {
            this.$emit('update:modelValue', newValue)
        }
    }
}
</script>

<style>

</style>