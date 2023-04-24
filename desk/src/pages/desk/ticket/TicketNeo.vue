<template>
	<div v-if="isResLoaded" class="flex flex-col">
		<TopBar />
		<div class="flex grow overflow-hidden">
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
import { ref } from "vue";
import { init } from "./data";
import CommunicationList from "./CommunicationList.vue";
import ResponseEditor from "./editor/ResponseEditor.vue";
import SideBar from "./SideBar.vue";
import TopBar from "./TopBar.vue";

const props = defineProps({
	ticketId: {
		type: String,
		required: true,
	},
});
const isResLoaded = ref(false);

init(parseInt(props.ticketId)).then(() => (isResLoaded.value = true));
</script>
