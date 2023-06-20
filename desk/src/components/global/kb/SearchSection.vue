<template>
	<div
		class="bg-gray-100 w-full flex items-center"
		:class="isRoot ? 'h-[350px]' : 'h-[236px]'"
	>
		<div class="container flex flex-col space-y-5 mx-auto">
			<div
				class="text-gray-900 font-semibold"
				:class="isRoot ? 'text-[52px]' : 'text-[36px]'"
			>
				{{ isRoot ? "How can I help you?" : "Knowledge Base" }}
			</div>
			<div class="flex flex-col">
				<Popover>
					<template #target="{ togglePopover }">
						<div>
							<div
								class="rounded-xl w-[600px] shadow bg-white h-10 flex flex-row items-center px-3 space-x-3"
							>
								<FeatherIcon
									name="search"
									class="h-4 w-4 stroke-gray-500"
								/>
								<input
									@input="
										($event) => {
											if ($event.target.value) {
												onSearch($event.target.value)
												togglePopover(true)
											} else {
												togglePopover(false)
											}
										}
									"
									:disabled="disabled"
									type="text"
									placeholder="Write a question or problem"
									class="grow text-sm text-left text-gray-500 border-0 focus:ring-0"
								/>
							</div>
						</div>
					</template>
					<template #body>
						<div
							class="text-base text-gray-700 shadow rounded bg-white mt-2 max-h-[300px] overflow-y-scroll"
						>
							<div v-if="searchResults.length > 0">
								<div
									v-for="(result, index) in searchResults"
									:key="result.name"
								>
									<RouterLink
										:to="{
											path: `/knowledge-base/${
												result.doctype === 'Article'
													? 'articles'
													: 'categories'
											}/${result.name}`,
										}"
										as="div"
									>
										<div
											class="p-2 hover:bg-gray-50 cursor-pointer"
											:class="
												index < searchResults.length - 1
													? 'border-b'
													: ''
											"
										>
											<div
												class="flex flex-row space-x-2 items-center"
											>
												<FeatherIcon
													:name="
														result.doctype ===
														'Article'
															? 'file-text'
															: 'folder'
													"
													class="h-4 w-4 stroke-gray-500"
												/>
												<div>{{ result.title }}</div>
											</div>
										</div>
									</RouterLink>
								</div>
							</div>
							<div v-else class="p-2 text-gray-500">
								<LoadingText
									v-if="$resources.searchResults.loading"
									text="Searching..."
								/>
								<div v-else>No Results Found</div>
							</div>
						</div>
					</template>
				</Popover>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, debounce, Popover, LoadingText } from "frappe-ui"
import { ref } from "vue"

export default {
	name: "KBSearchSection",
	props: {
		isRoot: {
			type: Boolean,
			default: false,
		},
		disabled: {
			type: Boolean,
			default: true,
		},
	},
	components: {
		FeatherIcon,
		Popover,
		FeatherIcon,
		LoadingText,
	},
	setup() {
		const searchText = ref("")

		return {
			searchText,
		}
	},
	computed: {
		searchResults() {
			if (!this.searchText) return []
			return this.$resources.searchResults.data || []
		},
	},
	methods: {
		onSearch: debounce(function (val) {
			this.searchText = val
			this.$resources.searchResults.submit({
				text: val,
			})
		}, 300),
	},
	resources: {
		searchResults: {
			url: "helpdesk.api.kb.search",
		},
	},
}
</script>
