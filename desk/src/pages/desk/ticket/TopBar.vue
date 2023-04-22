<template>
	<div class="flex flex-col justify-center border-b border-gray-100 px-5 py-3">
		<div class="line-clamp-1 text-xl font-medium text-gray-900">
			{{ ticket?.doc?.subject }}
		</div>
		<div class="flex items-center gap-1 text-base text-gray-600">
			<IconHash />
			{{ ticket?.doc?.name }}
			<IconDot />
			Last modified on {{ modifiedDay }} at {{ modifiedTime }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import dayjs from "dayjs";
import { ticket } from "./data";
import IconHash from "~icons/espresso/hash";
import IconDot from "~icons/ph/dot-outline-fill";

const modified = computed(() =>
	dayjs(ticket.value?.doc?.modified).tz(dayjs.tz.guess())
);
const modifiedDay = computed(() => modified.value.format("D MMMM YYYY"));
const modifiedTime = computed(() => modified.value.format("h:mm A"));
</script>
