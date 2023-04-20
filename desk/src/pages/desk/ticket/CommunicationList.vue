<template>
	<div class="flex flex-col items-center overflow-scroll">
		<div class="content flex flex-col gap-4">
			<CommentItem />
			<ConversationItem />
			<CommentItem />
			<ConversationItem />
			<CommentItem />
			<ConversationItem />
			<CommentItem />
		</div>
		<div class="grow"></div>
	</div>
</template>

<script setup lang="ts">
import CommentItem from "./CommentItem.vue";
import ConversationItem from "./ConversationItem.vue";
</script>

<style scoped>
.content {
	width: 742px;
}
</style>
