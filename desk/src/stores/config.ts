import { computed, ComputedRef, ref } from "vue";
import { defineStore } from "pinia";
import { createResource } from "frappe-ui";
import { useTitle } from "@vueuse/core";
import { socket } from "@/socket";

const URI_CONFIG = "helpdesk.api.config.get_config";
const DEFAULT_TITLE = "Helpdesk";

export const useConfigStore = defineStore("config", () => {
	const configRes = createResource({
		url: URI_CONFIG,
		auto: true,
	});

	const config = computed(() => configRes.data || {});
	const brandLogo = computed(() => config.value.brand_logo);
	const helpdeskName: ComputedRef<string> = computed(
		() => config.value.helpdesk_name || DEFAULT_TITLE
	);
	const suppressEmailToast: ComputedRef<boolean> = computed(
		() => config.value.suppress_default_email_toast ?? true
	);
	const pageTitle = ref(null);
	const windowTitle = computed(() =>
		pageTitle.value
			? `${pageTitle.value} | ${helpdeskName.value}`
			: helpdeskName.value
	);

	function setTitle(title?: string) {
		pageTitle.value = title ? title : null;
	}

	useTitle(windowTitle);

	socket.on("helpdesk:settings-updated", () => configRes.reload());

	return {
		config,
		brandLogo,
		helpdeskName,
		suppressEmailToast,

		setTitle,
	};
});
