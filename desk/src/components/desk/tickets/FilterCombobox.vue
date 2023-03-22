<template>
	<div>
		<Listbox v-model="selected">
			<div>
				<ListboxButton class="flex gap-1 rounded-lg bg-gray-200 px-2 py-1">
					<div class="flex content-start truncate" :class="buttonClass">
						{{ selected.label }}
					</div>
					<FeatherIcon name="chevron-down" class="h-5 w-5" />
				</ListboxButton>
			</div>
			<div class="absolute z-20 pt-2">
				<transition
					enter-active-class="transition duration-200 ease-out"
					enter-from-class="translate-y-1 opacity-0"
					enter-to-class="translate-y-0 opacity-100"
					leave-active-class="transition duration-150 ease-in"
					leave-from-class="translate-y-0 opacity-100"
					leave-to-class="translate-y-1 opacity-0"
				>
					<ListboxOptions>
						<div>
							<div
								class="max-h-64 overflow-x-scroll rounded-lg border border-gray-300 bg-white px-1 py-2 shadow-black drop-shadow-xl"
							>
								<ListboxOption
									v-for="o in options"
									v-slot="{ active }"
									:key="o.value"
									:value="o"
									class="bg-white"
								>
									<div
										class="cursor-pointer rounded-lg px-2 py-1"
										:class="active ? 'bg-gray-200' : ''"
									>
										{{ o.label }}
									</div>
								</ListboxOption>
							</div>
						</div>
					</ListboxOptions>
				</transition>
			</div>
		</Listbox>
	</div>
</template>

<script setup lang="ts">
import {
	defineEmits,
	defineProps,
	ref,
	toRefs,
	unref,
	watch,
	PropType,
} from "vue";
import {
	Listbox,
	ListboxButton,
	ListboxOptions,
	ListboxOption,
} from "@headlessui/vue";
import { FeatherIcon } from "frappe-ui";

type InputItem = {
	label: string;
	value: string;
};

const props = defineProps({
	options: {
		type: Array<InputItem>,
		required: true,
	},
	defaultSelected: {
		type: Object as PropType<InputItem>,
		required: false,
		default: null,
	},
	buttonClass: {
		type: String,
		required: false,
		default: "",
	},
});
const emit = defineEmits(["selection-update"]);
const { options, defaultSelected } = toRefs(props);
const selected = ref(unref(defaultSelected) || [...unref(options)].shift());

emit("selection-update", selected.value);
watch(selected, (v) => emit("selection-update", v));
</script>
