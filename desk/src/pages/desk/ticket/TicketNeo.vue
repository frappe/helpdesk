<template>
	<div class="flex flex-col">
		<TopBar v-bind="topbarProps" />
		<div class="flex overflow-hidden">
			<div class="flex grow flex-col">
				<CommunicationList />
				<div class="grow"></div>
				<ResponseEditor />
			</div>
			<SideBar />
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ComputedRef, toRefs } from "vue";
import { createDocumentResource } from "frappe-ui";
import CommunicationList from "./CommunicationList.vue";
import ResponseEditor from "./ResponseEditor.vue";
import SideBar from "./SideBar.vue";
import TopBar from "./TopBar.vue";

const props = defineProps({
	ticketId: {
		type: Number,
		required: true,
	},
});

const { ticketId } = toRefs(props);

const t__ = createDocumentResource({
	doctype: "HD Ticket",
	name: ticketId,
	// fields: ["*"],
	auto: true,
});

const ticket = computed(() => t__.doc || {});
const title: ComputedRef<string> = computed(() => ticket.value.subject || "");

const topbarProps = {
	id: ticketId,
	title,
};
</script>
