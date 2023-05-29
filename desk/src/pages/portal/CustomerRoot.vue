<template>
	<div>
		<div class="h-15 border-b">
			<NavBar />
		</div>
		<router-view class="mb-10" />
	</div>
</template>

<script setup lang="ts">
import NavBar from "@/components/portal/NavBar.vue";
</script>
