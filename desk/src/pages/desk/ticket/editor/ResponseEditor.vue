<template>
	<div class="content mx-auto">
		<div class="my-3.5 ml-2 flex items-start gap-2 pl-2">
			<Avatar
				:image-u-r-l="authStore.userImage"
				:label="authStore.userName"
				size="md"
			/>
			<div
				v-if="!responseEditor.isExpanded"
				class="flex h-8 w-full cursor-pointer select-none items-center rounded-lg border border-gray-300 px-2.5 text-base text-gray-500"
				@click="responseEditor.isExpanded = true"
			>
				{{ placeholder }}
			</div>
			<div v-if="responseEditor.isExpanded" class="editor-shadow grow">
				<TextEditor
					editor-class="prose-sm max-w-none p-3 overflow-auto h-32 focus:outline-none"
					:mentions="mentions"
					:placeholder="placeholder"
					:content="responseEditor.content"
					@change="(v) => (responseEditor.content = v)"
				>
					<template #top>
						<TopSection />
					</template>
					<template #editor="{ editor }">
						<TextEditorContent :editor="editor" />
					</template>
					<template #bottom>
						<BottomSection />
					</template>
				</TextEditor>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onUnmounted } from "vue";
import { Avatar, TextEditor, TextEditorContent } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useAgentStore } from "@/stores/agent";
import { responseEditor } from "../data";
import BottomSection from "./BottomSection.vue";
import TopSection from "./TopSection.vue";

const authStore = useAuthStore();
const agentStore = useAgentStore();
const placeholder = "Add a reply / comment";
const mentions = computed(() =>
	agentStore.options.map((a) => ({
		label: a.agent_name,
		value: a.name,
	}))
);

onUnmounted(() => (responseEditor.isExpanded = false));
</script>

<style scoped>
.content {
	width: 742px;
}

.editor-shadow {
	box-shadow: 0px 0px 1px rgba(0, 0, 0, 0.45), 0px 1px 2px rgba(0, 0, 0, 0.1);
	border-radius: 12px;
}
</style>
