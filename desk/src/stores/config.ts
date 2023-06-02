import { computed, ComputedRef, ref } from "vue";
import { defineStore } from "pinia";
import { createResource } from "frappe-ui";
import { useFavicon } from "@vueuse/core";
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
	const brandFavicon = computed(() => config.value.brand_favicon);
	const helpdeskName: ComputedRef<string> = computed(
		() => config.value.helpdesk_name || DEFAULT_TITLE
	);
	const isSetupComplete: ComputedRef<boolean> = computed(
		() => config.value.is_setup_complete
	);
	const skipEmailWorkflow: ComputedRef<string> = computed(
		() => config.value.skip_email_workflow
	);
	const pageTitle = ref(null);
	const windowTitle = computed(() =>
		pageTitle.value
			? `${pageTitle.value} • ${helpdeskName.value}`
			: helpdeskName.value
	);

	function setTitle(title?: string) {
		pageTitle.value = title ? title : null;
	}

	useFavicon(brandFavicon);
	useTitle(windowTitle);

	socket.on("helpdesk:settings-updated", () => configRes.reload());

	return {
		brandLogo,
		config,
		helpdeskName,
		isSetupComplete,
		setTitle,
		skipEmailWorkflow,
	};
});
