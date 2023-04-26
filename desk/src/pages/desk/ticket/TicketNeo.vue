<template>
	<div v-if="isResLoaded" class="flex flex-col">
		<TopBar />
		<div class="flex grow overflow-hidden">
			<div class="flex grow flex-col">
				<ConversationBox />
				<div class="grow"></div>
				<ResponseEditor />
			</div>
			<SideBar />
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from "vue";
import { useConfigStore } from "@/stores/config";
import { clean, init, ticket } from "./data";
import ConversationBox from "./ConversationBox.vue";
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
const configStore = useConfigStore();

init(parseInt(props.ticketId)).then(() => {
	configStore.setTitle(ticket.doc.subject);
	isResLoaded.value = true;
});

onUnmounted(() => {
	clean();
	configStore.setTitle();
});
</script>
