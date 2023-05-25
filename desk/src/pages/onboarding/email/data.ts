import { ref } from "vue";
import { defineStore } from "pinia";

export const useOnboardingEmailStore = defineStore("onboarding", () => {
	const step = ref(0);
	const service = ref("");

	function next() {
		step.value++;
	}

	return {
		next,
		service,
		step,
	};
});
