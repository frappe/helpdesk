<template>
	<div class="flex flex-col space-y-4">
		<div v-if="editable" class="flex flex-row items-center">
			<slot name="top-left-section">
				<div v-if="!editMode"><LayoutSwitcher viewMode="Web" /></div>
				<div v-else class="text-base text-gray-700 italic">
					Editing - Knowledge Base
				</div>
			</slot>
			<div class="grow" />
			<div v-if="editMode" class="flex flex-row-reverse">
				<Button
					:loading="saveInProgress"
					icon-left="save"
					class="ml-2"
					:class="disableSaving ? 'cursor-not-allowed' : ''"
					:disable="disableSaving"
					@click="$emit('save')"
				>
					Save
				</Button>
				<Button icon-left="rotate-ccw" @click="$emit('discard')">
					Discard
				</Button>
			</div>
			<div v-else>
				<Button icon-left="edit-2" @click="$emit('edit')">
					Edit
				</Button>
			</div>
		</div>
		<slot class="h-full" name="body" />
	</div>
</template>

<script>
import LayoutSwitcher from "@/components/global/kb/LayoutSwitcher.vue"

export default {
	name: "EditableBlock",
	props: {
		editable: {
			type: Boolean,
			default: false,
		},
		editMode: {
			type: Boolean,
			default: false,
		},
		saveInProgress: {
			type: Boolean,
			default: false,
		},
		disableSaving: {
			type: Boolean,
			default: false,
		},
	},
	components: {
		LayoutSwitcher,
	},
}
</script>
