import { ComputedRef, ref, Ref } from "vue";
import { defineStore } from "pinia";
import { useMagicKeys } from "@vueuse/core";
import { isEqual } from "lodash";

type KeyCombination = Array<string>;
type Handler = () => void;
type Help = string;

const isMac = navigator.userAgent.indexOf("Mac OS X") != -1;
const controlKey = isMac ? "⌃" : "Ctrl";
const altKey = isMac ? "⌥" : "Alt";
const metaKey = isMac ? "⌘" : "Meta";

class Shortcut {
	constructor(
		public isActive: ComputedRef<boolean>,
		public keyCombination: KeyCombination,
		public handler: Handler,
		public help?: Help
	) {}

	comboString() {
		return this.keyCombination
			.map((k) =>
				k
					.replaceAll("Control", controlKey)
					.replaceAll("Alt", altKey)
					.replaceAll("Meta", metaKey)
			)
			.join(" + ");
	}
}

export const useKeymapStore = defineStore("keymap", () => {
	const keys = useMagicKeys({
		passive: false,
		onEventFired(e) {
			const k = items.value.find((item) => item.isActive);
			if (!k) return;

			e.preventDefault();
			k.handler();
		},
	});
	const items: Ref<Array<Shortcut>> = ref([]);
	const isOpen = ref(false);

	function add(combination: KeyCombination, handler: Handler, help?: Help) {
		const combo = Array.isArray(combination) ? combination : [combination];
		const isActive = keys[combo.join("+")];
		const s = new Shortcut(isActive, combo, handler, help);

		remove(combo);
		items.value.push(s);
	}

	function remove(combo: KeyCombination) {
		items.value = items.value.filter((s) => !isEqual(s.keyCombination, combo));
	}

	function toggleVisibility(open?: boolean) {
		isOpen.value = open ?? !isOpen.value;
	}

	return {
		add,
		isOpen,
		items,
		remove,
		toggleVisibility,
	};
});
