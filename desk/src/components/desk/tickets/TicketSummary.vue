<template>
	<div class="leading-loose">
		{{ subject }}
		<div class="flex flex-wrap items-center gap-3">
			<div>{{ name }}</div>
			<div>&#2022</div>
			<div class="flex gap-1">
				<FeatherIcon name="mail"/> {{ emailCount }}
			</div>
			<div>&#2022</div>
			<div class="flex gap-1">
				<FeatherIcon name="message-circle"/> {{ commentCount }}
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { defineProps, ref, toRefs } from 'vue';
import { FeatherIcon, createDocumentResource } from 'frappe-ui';

const props = defineProps({
	ticketName: {
		type: String,
		required: true
	}
});

const { ticketName } = toRefs(props);
const subject = ref("")
const name = ref("")
const emailCount = ref(0)
const commentCount = ref(0)

createDocumentResource({
	doctype: 'Ticket',
	name: ticketName,
	onSuccess: (data: any) => {
		subject.value = data.subject;
		name.value = data.name;
	},
	auto: true,
	cache: ["Ticket", ticketName],
});
</script>
