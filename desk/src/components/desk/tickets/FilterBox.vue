<template>
	<div>
		<Popover>
			<div>
				<PopoverButton
					class="flex select-none items-center gap-1 rounded-lg border border-gray-300 px-2 py-1 text-base"
				>
					<FeatherIcon name="filter" class="h-3 w-3" />
					Filters
				</PopoverButton>
			</div>
			<transition
				enter-active-class="transition duration-200 ease-out"
				enter-from-class="translate-y-1 opacity-0"
				enter-to-class="translate-y-0 opacity-100"
				leave-active-class="transition duration-150 ease-in"
				leave-from-class="translate-y-0 opacity-100"
				leave-to-class="translate-y-1 opacity-0"
			>
				<PopoverPanel
					class="absolute right-2 z-10 m-3 w-max rounded-lg border border-gray-300 bg-white shadow-black drop-shadow-xl"
				>
					<div class="flex flex-col gap-2 p-2 text-base">
						<div v-for="(f, i) in filters" :key="i">
							<div class="flex items-center justify-between gap-2">
								<FilterCombobox
									:options="fields"
									:default-selected="
										fields.find((filter) => filter.value === f.fieldname)
									"
									button-class="w-20"
									@selection-update="(v) => (f.fieldname = v.value)"
								/>
								<FilterCombobox
									:options="operators"
									:default-selected="
										operators.find(
											(operator) => operator.value === f.filter_type
										)
									"
									button-class="w-12"
									@selection-update="(v) => (f.filter_type = v.value)"
								/>
								<Input
									class="rounded-lg bg-gray-200"
									:value="f.value"
									@input="(v: string) => (f.value = v)"
								/>
								<Button
									icon-left="x"
									class="bg-white hover:bg-white"
									@click="() => removeFilter(i)"
								/>
							</div>
						</div>
						<div class="flex justify-between gap-1">
							<Button
								icon-left="plus"
								class="rounded-lg bg-white"
								@click="addFilter"
								>Add Filter</Button
							>
							<Button
								v-if="!isEmpty(filters)"
								icon-left="check"
								class="rounded-lg bg-white"
								@click="applyFilters"
								>Apply Filters</Button
							>
							<Button
								v-if="!isEmpty(filters)"
								icon-left="x"
								class="rounded-lg bg-white"
								@click="clearFilters"
								>Clear Filters</Button
							>
						</div>
					</div>
				</PopoverPanel>
			</transition>
		</Popover>
	</div>
</template>

<script setup lang="ts">
import { isEmpty } from "lodash";
import { Ref, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue";
import { FeatherIcon } from "frappe-ui";
import { useListFilters, FilterItem } from "@/composables/listFilters";
import FilterCombobox from "./FilterCombobox.vue";

const router = useRouter();
const filters: Ref<Array<FilterItem>> = ref([]);
const listFilters = useListFilters();

const fields = [
	{
		label: "Status",
		value: "status",
	},
	{
		label: "Assigned To",
		value: "_assign",
	},
	{
		label: "Priority",
		value: "priority",
	},
];

const operators = [
	{
		value: "=",
		label: "Equal",
	},
	{
		value: "!=",
		label: "Not Equal",
	},
	{
		value: ">",
		label: "Greater Than",
	},
	{
		value: ">=",
		label: "Greater Than or Equal",
	},
	{
		value: "<",
		label: "Less Than",
	},
];

function addFilter() {
	filters.value.push({});
}

function removeFilter(index: number) {
	filters.value.splice(index, 1);
	if (isEmpty(filters.value)) clearFilters();
}

function clearFilters() {
	filters.value = [];
	router.push({ query: { q: "" } });
}

function applyFilters() {
	const f = filters.value
		.filter((f) => f.fieldname)
		.filter((f) => f.value)
		.filter((f) => f.filter_type);

	listFilters.applyQuery(listFilters.toQuery(f));
}

onMounted(() => {
	const fromQuery = listFilters.fromQuery();
	if (isEmpty(fromQuery)) return;
	filters.value = fromQuery;
});
</script>
