<template>
	<KBEditableBlock
		class="h-full"
		:editable="editable"
		:editMode="editMode"
		:saveInProgress="saveInProgress"
		:disableSaving="disableSaving"
		@edit="() => {
			editMode = true
		}"
		@discard="() => {
			editMode = false
		}"
		@save="() => {
			if(validateChanges()) {
				saveChanges().then(() => {
					editMode = false
				})
			}
		}"
	>
		<template #body>
			<div :class="editable ? `rounded shadow p-5 h-full overflow-y-scroll ${ editMode ? 'border-2 border-gray-300' : ''}` : ''">
				<div class="grid grid-cols-1 place-content-center gap-10">
					<div class="grid place-content-center gap-5 text-center bg-gray-100 w-full h-[250px]">
						<div class="text-[36px] text-gray-900 font-semibold">How can I help you?</div>
						<div class="rounded-xl max-w-3xl shadow bg-white h-10 flex flex-row items-center px-3 space-x-3">
							<FeatherIcon name="search" class="h-4 w-4 stroke-gray-500"/>
							<div class="grow text-[12px] text-left text-gray-500">Write a question or problem</div>
						</div>
					</div>
					<div class="flex flex-col space-y-7">
						<CategoryCardList as="div"
							v-if="!(parentCategoryId && categoryId)"
							ref="categoryCardList"
							:editable="editable"
							:editMode="editMode"
							:categoryId="categoryId"
							:parentCategoryId="parentCategoryId"
						/>
						<ArticleMiniList as="div"
							v-if="!isRoot"
							ref="articleMiniList"
							:editable="editable"
							:editMode="editMode"
							:categoryId="categoryId"
						/>
						<!-- <FAQList :editable="editable" v-else>
							TODO: Show FAQ edit list
						</FAQList> -->
					</div>
				</div>
			</div>
		</template>
	</KBEditableBlock>
</template>

<script>
import { FeatherIcon } from 'frappe-ui';
import { provide, ref } from 'vue'
import { useRoute } from 'vue-router'
import CategoryCardList from '@/components/global/CategoryCardList.vue'
import ArticleMiniList from '@/components/global/ArticleMiniList.vue'
import KBEditableBlock from '@/components/global/KBEditableBlock.vue'

export default {
	name: 'KBHome',
	props: {
		categoryId: {
			type: String,
			default: null
		},
		parentCategoryId: {
			type: String,
			default: null
		}
	},
	components: {
		FeatherIcon,
		CategoryCardList,
		ArticleMiniList,
		KBEditableBlock
	},
	setup(props) {
		const route = useRoute()
		const editable = ref(route.meta.editable)

		provide('categoryId', props.categoryId)
		if (props.parentCategoryId) {
			provide('parentCategoryId', props.parentCategoryId)
		}

		const editMode = ref(false)
		const saveInProgress = ref(false)

		return {
			editable,
			editMode,

			saveInProgress
		}
	},
	computed: {
		disableSaving() {
			// TODO: check of validation errors etc
			return false
			// return this.$refs.categoryCardList?.disableSaving // || this.$refs.articleMiniList?.disableSaving
		},
		isRoot() {
			return !this.categoryId && !this.parentCategoryId
		}
	},
	methods: {
		validateChanges() {
			return this.$refs.categoryCardList.validateChanges() && this.$refs.articleMiniList ? this.$refs.articleMiniList.validateChanges() : true
		},
		async saveChanges() {
			this.saveInProgress = true
			await this.$refs.categoryCardList.saveChanges()
			if (this.$refs.articleMiniList) await this.$refs.articleMiniList.saveChanges()
			this.saveInProgress = false
			return
		}
	}
}
</script>