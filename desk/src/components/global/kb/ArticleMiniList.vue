<template>
	<!-- TODO: option to add articles via combobox, create new articles too ? -->
	<div
		v-if="categoryId && (articles?.length > 0 || editMode)"
		class="flex flex-col space-y-5"
	>
		<div class="flex flex-row items-center space-x-2">
			<div class="text-3xl font-bold text-gray-800">{{ categoryName }}</div>
			<!-- TODO: <FeatherIcon v-if="editMode" name="plus" class="w-4 cursor-pointer my-auto bg-gray-50 hover:bg-gray-100 rounded" /> -->
			<p v-if="editMode" class="text-base text-gray-500">
				( add articles from
				<RouterLink class="underline" :to="{ path: '/kb/articles' }"
					>here</RouterLink
				>
				)
			</p>
		</div>
		<draggable
			:list="articles"
			:disabled="!editMode"
			item-key="idx"
			class="grid grow place-content-center gap-y-3"
			:class="articles?.length > 6 ? 'grid-cols-2' : 'grid-cols-1'"
		>
			<template #item="{ element }">
				<div class="flex flex-row items-center space-x-1">
					<ArticleMiniListItem
						:article="element"
						@click="
							() => {
								if (editMode) return;
								$router.push({
									path: `/${
										$route.meta.editable ? 'kb' : 'knowledge-base'
									}/articles/${element.name}/${element.title_slug}`,
								});
							}
						"
					/>
				</div>
			</template>
		</draggable>
	</div>
</template>

<script>
import { ref, provide, computed, inject } from "vue";
import draggable from "vuedraggable";
import ArticleMiniListItem from "@/components/global/kb/ArticleMiniListItem.vue";
import { FeatherIcon } from "frappe-ui";

export default {
	name: "ArticleMiniList",
	components: {
		draggable,
		ArticleMiniListItem,
		FeatherIcon,
	},
	props: {
		categoryId: {
			type: String,
			default: null,
		},
	},
	setup(props, context) {
		const tempArticles = ref([]);
		const allValidationErrors = ref([]);

		provide("allValidationErrors", allValidationErrors);

		const resources = ref(null);

		const saveInProgress = computed(() => {
			return resources.value.saveArticles.loading;
		});
		const validateChanges = () => {
			return allValidationErrors.value.length == 0;
		};
		const saveChanges = async () => {
			if (!props.categoryId) return;
			await resources.value.saveArticles.submit({
				new_values: tempArticles.value,
			});
		};

		const editMode = inject("editMode");

		const list = ref({
			loading: true,
			data: [],
		});

		context.expose({
			list,
			saveInProgress,
			validateChanges,
			saveChanges,
		});

		return {
			list,
			tempArticles,
			allValidationErrors,
			resources,
			editMode,
		};
	},
	computed: {
		articles() {
			if (this.editMode) return this.tempArticles;

			this.list.loading = this.$resources.articles.loading;
			this.list.data = this.$resources.articles.data || [];

			return this.list.data;
		},
		category() {
			return this.$resources.category.doc;
		},
		categoryName() {
			return this.category?.category_name || "Articles";
		},
	},
	watch: {
		editMode(newVal) {
			if (newVal) {
				this.tempArticles = JSON.parse(
					JSON.stringify(this.$resources.articles.data)
				);
			}
		},
	},
	mounted() {
		this.resources = this.$resources;
	},
	expose: ["articles"],
	resources: {
		articles() {
			const filters = { category: this.categoryId, status: "Published" };

			return {
				cache: ["Articles", this.categoryId, "published"],
				url: "helpdesk.api.kb.get_articles",
				params: {
					filters,
					limit: 999,
					order_by: "idx",
				},
				auto: true,
			};
		},
		saveArticles() {
			return {
				url: "helpdesk.api.kb.update_articles_order_and_status",
				onSuccess: () => {
					this.$resources.articles.reload();

					this.$toast({
						title: "Articles updated!!",
						icon: "check",
						iconClasses: "text-green-500",
					});
				},
				onError: (err) => {
					this.$toast({
						title: "Error while saving",
						text: err,
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
			};
		},
		category() {
			return {
				type: "document",
				doctype: "HD Article Category",
				name: this.categoryId,
			};
		},
	},
};
</script>
