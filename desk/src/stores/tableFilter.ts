import { ref, watch, Ref } from "vue";
import { defineStore } from "pinia";

interface FilterEntry {
	[key:string]: {
		available: Array<Array<string>>
		active: Array<string>
	}
}

export const useTableFilterStore = defineStore("tableFilter", () => {
	const data: Ref<FilterEntry> = ref();

	function createTableEntry(table: string) {
		if (data[table]) return;

		data[table] = {
			available: [],
			active: [],
		}
	}

	function setFilters(table: string, filters: Array<Array<string>>) {
		createTableEntry(table);
		data[table].available = filters;
	}

	function setActiveFilter(table: string, filter: Array<string>) {
		createTableEntry(table);
        data[table].active = filter;
	}

	function getActiveFilter(table: string) {
		createTableEntry(table);
		return data[table].active;
    }

	return {
		data,
		getActiveFilter,
		setActiveFilter,
		setTableFilter: setFilters,
	}
});
