<template>
	<div class="flex flex-col">
		<div class="h-12">
			<div v-if="editable" class="flex flex-row items-center">
				<div class="grow text-xl">Knowledge Base</div>
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
				<div v-else class="flex flex-row-reverse items-center">
					<KBLayoutSwitcher viewMode="Web" class="ml-2" />
					<Button icon-left="edit-2" @click="$emit('edit')">
						Edit
					</Button>
				</div>
			</div>
		</div>
		<slot class="h-full" name="body" />
	</div>
</template>

<script>
import KBLayoutSwitcher from "@/components/global/KBLayoutSwitcher.vue"

export default {
	name: "KBEditableBlock",
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
		KBLayoutSwitcher,
	},
}
</script>
