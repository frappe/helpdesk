<template>
	<div class="mx-auto w-full h-screen p-4">
		<div class="rounded shadow p-5 h-full overflow-y-scroll">
			<KBHome v-if="viewMode == 'website'" :editable="true"/>
		</div>
	</div>
</template>

<script>
import { ref } from 'vue';
import KBHome from '@/components/global/KBHome.vue';

export default {
	name: 'KnowledgeBase',
	components: {
		KBHome
	},
	setup() {
		const viewMode = ref('website'); // website or list

		return {
			viewMode,
		};
	}
}
</script>