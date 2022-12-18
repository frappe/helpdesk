<template>
	<div>
		<Dialog
			:options="{ title: '&nbsp;', size: '2xl' }"
			:show="show"
			@close="close()"
		>
			<template #body-content>
				<div
					class="border-b border-grey-400 w-full pl-2 pb-4 absolute left-0 top-0 px-4 py-3 sm:px-6 flex justify-between items-center"
				>
					<div class="">Articles</div>
					<Button
						icon="x"
						class="bg-transparent w-2 h-2"
						@click="close()"
					/>
				</div>
				<div
					class="w-full border bg-[#EBEEF0] h-8 flex flex-row items-center space-x-3 mt-5 rounded mb-3"
				>
					<FeatherIcon
						name="search"
						class="h-4 w-4 stroke-gray-500 ml-[8px]"
					/>
					<Input
						v-model="search"
						id="searchInput"
						class="grow text-[12px] text-left text-black border-0 bg-[#EBEEF0] h-[31px] rounded-none pl-0"
						type="text"
						placeholder="Search for response"
						@input="getArticles"
					/>
				</div>
				<div
					class="divide-y divide-slate-200 max-h-[256px] overflow-y-scroll"
				>
					<div
						v-for="item in this.articleResponses"
						class="relative py-3"
					>
						<CustomIcons
							name="add-new"
							class="h-7 w-7 rounded p-1 mb-4 absolute right-0"
							role="button"
							@click="
								() => {
									addContent(item)
									emitContent()
									close()
								}
							"
						/>
						<Accordion class="my-2">
							<template v-slot:title>
								<span class="font-medium text-lg">{{
									item.title
								}}</span>
							</template>
							<template v-slot:content>
								<div
									v-html="item.content"
									class="ProseMirror prose font-normal text-lg text-slate-500 ml-5 mt-4"
								></div>
							</template>
						</Accordion>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Dialog, FeatherIcon, Input, Button } from "frappe-ui"
import Accordion from "@/components/global/Accordion.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { ref, computed, provide } from "vue"
export default {
	name: "ArticleResponseDialog",
	props: ["show"],
	components: {
		Dialog,
		FeatherIcon,
		Accordion,
		CustomIcons,
	},
	setup() {
		const listManager = ref([])
		const tempContent = ref("")
		provide("tempContent", tempContent)
		return {
			listManager,
			tempContent,
		}
	},
	data() {
		return {
			articleResponses: [],
		}
	},
	methods: {
		close() {
			this.$emit("close")
			this.$emit("contentVal", this.tempContent)
		},
		emitContent() {
			this.$emit("ContentVal", this.tempContent)
		},
		addContent(item) {
			this.tempContent = item.content
		},
		getArticles(event) {
			let title = event
			this.$resources.list.fetch({
				title: title,
			})
		},
	},
	resources: {
		list() {
			return {
				method: "frappedesk.api.kb.get_articles_in_ticket",
				onSuccess(val) {
					this.articleResponses = val
					return this.articleResponses
				},
			}
		},
	},
	beforeMount() {
		this.getArticles()
	},
}
</script>
