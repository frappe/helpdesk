<template>
	<Autocomplete
		:options="options"
		:value="defaultOption"
		@update:query="(q) => onUpdateQuery(q)"
	/>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createListResource, Autocomplete } from "frappe-ui";

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	searchField: {
		type: String,
		required: false,
		default: "name",
	},
	labelField: {
		type: String,
		required: false,
		default: "name",
	},
	valueField: {
		type: String,
		required: false,
		default: "name",
	},
	pageLength: {
		type: Number,
		required: false,
		default: 10,
	},
});

const r = createListResource({
	doctype: props.doctype,
	pageLength: props.pageLength,
	auto: true,
	fields: [props.labelField, props.searchField, props.valueField],
});
const options = computed(
	() =>
		r.data?.map((result) => ({
			label: result[props.labelField],
			value: result[props.valueField],
		})) || []
);
const defaultOption = computed(() => [...options.value].shift());

function onUpdateQuery(query: string) {
	r.update({
		filters: {
			[props.searchField]: ["like", `%${query}%`],
		},
	});

	r.reload();
}
</script>
