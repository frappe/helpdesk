<template>
	<div class="border-b border-gray-100 py-3">
		<div class="flex items-center">
			<IconCaretLeft
				class="ml-5 mr-2 h-4 w-4 cursor-pointer text-gray-700"
				@click="goBack"
			/>
			<div class="line-clamp-1 text-xl font-medium text-gray-900">
				{{ ticket.doc.subject }}
			</div>
		</div>
		<div class="ml-11 flex items-center gap-1 text-base text-gray-600">
			<div class="flex">
				<Tooltip
					v-if="ticket.doc.via_customer_portal"
					text="Created via customer portal"
				>
					<IconWeb />
				</Tooltip>
				<Tooltip v-else text="Created via email">
					<IconAtSign />
				</Tooltip>
				<IconDot />
			</div>
			<IconHash />
			<div class="cursor-copy" @click="copyId">
				{{ ticket.doc.name }}
			</div>
			<IconDot />
			Last modified
			<Tooltip :text="dateLong">
				{{ dateShort }}
			</Tooltip>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Tooltip } from "frappe-ui";
import { useClipboard } from "@vueuse/core";
import dayjs from "dayjs";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { useTicketStore } from "./data";
import { createToast } from "@/utils/toasts";
import IconAtSign from "~icons/espresso/at-sign";
import IconCaretLeft from "~icons/ph/caret-left";
import IconDot from "~icons/ph/dot-bold";
import IconHash from "~icons/espresso/hash";
import IconWeb from "~icons/espresso/web";

const { copy } = useClipboard();
const router = useRouter();
const { ticket } = useTicketStore();

const date = computed(() => dayjs(ticket.doc.modified).tz(dayjs.tz.guess()));
const dateShort = computed(() => date.value.fromNow());
const dateLong = computed(() => date.value.format("dddd, MMMM D, YYYY h:mm A"));

async function copyId() {
	await copy(ticket.doc.name);

	createToast({
		title: "Copied to clipboard",
		icon: "check",
		iconClasses: "text-green-600",
	});
}

function goBack() {
	function fallback() {
		router.push({ name: AGENT_PORTAL_TICKET_LIST });
	}

	const previousPage = window.history.state.back;
	if (!previousPage) fallback();

	const route = router.resolve({ path: window.history.state.back });

	if (route.name === AGENT_PORTAL_TICKET_LIST) router.back();
	else fallback();
}
</script>
