<template>
	<div 
		class="flex flex-col" 
		:class="editMode ? 'border-2 border-gray-300 rounded p-5 space-y-4 mt-5' : ''"
	>
		<div class="h-12">
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
				<Button 
					icon-left="rotate-ccw" 
					@click="$emit('discard')"
				>
					Discard
				</Button>
			</div>
			<div v-else-if="editable" class="flex flex-row-reverse py-2">
				<Button 
					icon-left="edit-2" 
					@click="$emit('edit')"
				>
					Edit
				</Button>
			</div>
		</div>
		<div>
			<slot name="body" />
		</div>
	</div>
</template>

<script>
export default {
	name: 'KBEditableBlock',
	props: {
		editable: {
			type: Boolean,
			default: false
		},
		editMode: {
			type: Boolean,
			default: false
		},
		saveInProgress: {
			type: Boolean,
			default: false
		},
		disableSaving: {
			type: Boolean,
			default: false
		},
	}
}
</script>