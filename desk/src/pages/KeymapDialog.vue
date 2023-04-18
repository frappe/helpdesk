<template>
	<Dialog
		v-model="keymapStore.isOpen"
		:options="{ title: 'Keyboard Shortcuts' }"
	>
		<template #body-content>
			<div v-if="!isEmpty(keymapStore.items)" class="py-5 text-base">
				<table class="w-full table-fixed border-collapse border">
					<tbody>
						<tr
							v-for="s in keymapStore.items"
							:key="s.comboString()"
							class="h-16 border-y"
						>
							<td class="w-28 border-r px-4">
								<span
									class="rounded bg-gray-100 p-1.5 text-gray-500 shadow shadow-gray-400"
								>
									{{ s.comboString() }}
								</span>
							</td>
							<td class="px-4">{{ s.help }}</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-else class="text-base text-gray-600">No shortcuts defined</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { isEmpty } from "lodash";
import { useKeymapStore } from "@/stores/keymap";

const keymapStore = useKeymapStore();
</script>
