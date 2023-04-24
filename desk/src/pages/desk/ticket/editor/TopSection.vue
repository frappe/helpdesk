<template>
	<div class="divide-y rounded-t-xl border-b">
		<div class="px-3.5 py-1.5 text-base">
			<div class="flex justify-between">
				<div class="flex items-center gap-4">
					<div class="text-gray-600">To:</div>
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
				</div>
				<div class="flex gap-2">
					<div class="rounded-md bg-gray-300 px-2 py-1 text-base text-gray-800">
						Cc
					</div>
					<div class="rounded-md bg-gray-300 px-2 py-1 text-base text-gray-800">
						Bcc
					</div>
				</div>
			</div>
		</div>
		<div class="px-3.5 py-1.5 text-base">
			<div class="flex items-start gap-4">
				<div class="text-gray-600">Cc:</div>
				<div class="flex flex-wrap gap-1">
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
					<UserBubble name="John Doe" image="https://picsum.photos/200" />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import UserBubble from "./UserBubble.vue";
</script>
