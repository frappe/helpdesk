<template>
	<Dialog
		:options="{ title: 'Canned Responses', size: '2xl' }"
		:show="show"
		@close="close()"
	>
		<template #body-content>
			<div class="my-2 flex w-full flex-row items-center rounded border">
				<FeatherIcon name="search" class="mx-2 h-4 w-4" />
				<Input
					v-model="searchTerm"
					class="h-8 w-full rounded-sm bg-white pl-0 text-gray-800 focus:bg-white"
					type="text"
					placeholder="Search"
				/>
			</div>
			<div class="flex flex-col gap-2 divide-y overflow-y-auto">
				<div v-for="item in responses" :key="item.name">
					<div class="flex justify-between">
						<Accordion class="my-2">
							<template #title>
								<span class="text-base font-medium">{{ item.title }}</span>
							</template>
							<template #content>
								<div
									class="prose text-base text-slate-500"
									v-html="item.message"
								></div>
							</template>
						</Accordion>
						<FeatherIcon
							name="plus"
							class="my-2 h-4 w-4 cursor-pointer rounded bg-gray-100"
							@click="addMessage(item)"
						/>
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { onBeforeMount, ref, computed, toRefs, Ref, watch } from "vue";
import { createResource, Dialog, FeatherIcon, Input } from "frappe-ui";
import { useTicketStore } from "../data";
import Accordion from "@/components/global/Accordion.vue";

const props = defineProps({
	show: {
		type: Boolean,
		required: true,
	},
});

const emit = defineEmits(["close"]);

const { show } = toRefs(props);
const { editor } = useTicketStore();

const r = createResource({
	url: "helpdesk.api.cannedResponse.get_canned_response",
});

const responses = computed(() => r.data || []);
const searchTerm: Ref<string> = ref("");

onBeforeMount(() => r.fetch());
watch(searchTerm, () => {
	r.update({ params: { title: searchTerm.value } });
	r.reload();
});

function close() {
	emit("close");
}

function addMessage(item) {
	editor.content = item.message;
	close();
}
</script>
