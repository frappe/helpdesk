<template>
	<div class="divide-y rounded-t-xl border-b">
		<div class="px-3.5 py-1.5 text-base">
			<div class="flex justify-between">
				<div class="flex items-center gap-4">
					<div class="w-6 text-gray-600">To:</div>
					<UserBubble :name="to" />
				</div>
				<div class="flex gap-2">
					<div
						class="cursor-pointer rounded-md px-2 py-1 text-base text-gray-800"
						:class="{
							'bg-gray-300': responseEditor.isCcVisible,
						}"
						@click="responseEditor.isCcVisible = !responseEditor.isCcVisible"
					>
						Cc
					</div>
					<div
						class="cursor-pointer rounded-md px-2 py-1 text-base text-gray-800"
						:class="{
							'bg-gray-300': responseEditor.isBccVisible,
						}"
						@click="responseEditor.isBccVisible = !responseEditor.isBccVisible"
					>
						Bcc
					</div>
				</div>
			</div>
		</div>
		<div v-if="responseEditor.isCcVisible" class="px-3.5 py-1.5 text-base">
			<div class="flex items-start gap-4">
				<div class="w-6 text-gray-600">Cc:</div>
				<div class="flex w-full flex-wrap gap-1">
					<UserBubble
						v-for="cc in responseEditor.cc"
						:key="cc"
						:name="cc"
						class="cursor-pointer hover:bg-red-300"
						@click="() => removeFromArray(responseEditor.cc, cc)"
					/>
					<Input
						class="min-w-min grow bg-white text-gray-800 focus:bg-white"
						@keyup.enter="(v) => addToArray(responseEditor.cc, v)"
						@keyup.space="(v) => addToArray(responseEditor.cc, v)"
					/>
				</div>
			</div>
		</div>
		<div v-if="responseEditor.isBccVisible" class="px-3.5 py-1.5 text-base">
			<div class="flex items-start gap-4">
				<div class="w-6 text-gray-600">Bcc:</div>
				<div class="flex w-full flex-wrap gap-1">
					<UserBubble
						v-for="bcc in responseEditor.bcc"
						:key="bcc"
						:name="bcc"
						class="cursor-pointer hover:bg-red-300"
						@click="() => removeFromArray(responseEditor.bcc, bcc)"
					/>
					<Input
						class="min-w-min grow bg-white text-gray-800 focus:bg-white"
						@keyup.enter="(v) => addToArray(responseEditor.bcc, v)"
						@keyup.space="(v) => addToArray(responseEditor.bcc, v)"
					/>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { responseEditor, ticket } from "../data";
import UserBubble from "./UserBubble.vue";

const to = computed(() => ticket.doc.raised_by);

function addToArray(array: Array<string>, el) {
	const value = el.target.value;
	if (array.indexOf(value) < 0) array.push(value);
	el.target.value = "";
}

function removeFromArray(array: Array<string>, item: string) {
	array.splice(array.indexOf(item), 1);
}
</script>
