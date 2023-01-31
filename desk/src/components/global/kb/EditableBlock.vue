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
			<slot> </slot>
			<div v-if="editMode" class="flex flex-row items-center space-x-2">
				<slot name="edit-actions">
					<slot
						name="discard-action"
						:discard="
							(params) => {
								$emit('discard', params)
							}
						"
					>
						<Button
							icon-left="rotate-ccw"
							@click="$emit('discard')"
						>
							Discard
						</Button>
					</slot>
					<slot
						name="save-action"
						:save="
							(params) => {
								$emit('save', params)
							}
						"
						:disableSaving="disableSaving"
						:saveInProgress="saveInProgress"
					>
						<Button
							:loading="saveInProgress"
							icon-left="save"
							:class="disableSaving ? 'cursor-not-allowed' : ''"
							:disable="disableSaving"
							@click="$emit('save')"
						>
							Save
						</Button>
					</slot>
					<slot name="other-edit-actions" />
				</slot>
			</div>
			<div v-else class="flex flex-row items-center space-x-2">
				<slot name="main-actions">
					<Button icon-left="edit" @click="$emit('edit')">
						Edit
					</Button>
					<slot name="other-main-actions" />
				</slot>
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
