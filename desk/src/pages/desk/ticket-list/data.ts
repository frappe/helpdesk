import { ref, reactive } from "vue";
import { useKeymapStore } from "@/stores/keymap";
import { createListManager } from "@/composables/listManager";

const KEYMAPS = [
	{
		button: "R",
		status: "Replied",
	},
	{
		button: "E",
		status: "Resolved",
	},
	{
		button: "C",
		status: "Closed",
	},
];
const KEYMAP_PREFIX = "Control";
const keymapStore = useKeymapStore();

export function init() {
	KEYMAPS.forEach((o) => {
		keymapStore.add(
			[KEYMAP_PREFIX, o.button],
			() => {
				selected.value.forEach((ticketId) => {
					ticketList.setValue.submit({
						name: ticketId,
						status: o.status,
					});
				});
			},
			`Set ticket as ${o.status.toLowerCase()}`
		);
	});
}

export function deinit() {
	KEYMAPS.forEach((o) => keymapStore.remove([KEYMAP_PREFIX, o.button]));
}

export const selected = ref(new Set());
export function toggleOne(value) {
	if (!selected.value.delete(value)) {
		selected.value.add(value);
	}
}
export function selectAll() {
	ticketList.list.data?.forEach((t) => selected.value.add(t.name));
}
export function deselectAll() {
	selected.value.clear();
}

export const ticketList = createListManager({
	doctype: "HD Ticket",
	pageLength: 20,
});

export const columns = reactive({
	"Due in": true,
	"Created on": false,
	"Last modified": false,
	Source: false,
});
