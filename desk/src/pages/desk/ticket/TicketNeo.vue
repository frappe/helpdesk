<template>
	<div class="flex flex-col">
		<TopBar />
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
import { init } from "./data";
import CommunicationList from "./CommunicationList.vue";
import ResponseEditor from "./ResponseEditor.vue";
import SideBar from "./SideBar.vue";
import TopBar from "./TopBar.vue";

const props = defineProps({
	ticketId: {
		type: String,
		required: true,
	},
});

init(parseInt(props.ticketId));
</script>
