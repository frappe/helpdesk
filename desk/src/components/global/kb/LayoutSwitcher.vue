<template>
	<div class="text-base rounded-md h-[30px] bg-gray-100 p-[3px] select-none">
		<div
			v-if="viewMode === 'Web'"
			class="flex flex-row items-center space-x-2"
		>
			<router-link
				:title="'Toggle List view'"
				:to="{
					path: `/frappedesk/knowledge-base/${selectedList.toLowerCase()}`,
				}"
			>
				<FeatherIcon
					role="button"
					name="list"
					class="h-5 w-5 ml-2 stroke-gray-500 hover:stroke-gray-900"
				/>
			</router-link>
			<div
				class="bg-white rounded-md shadow px-2 py-0.5 w-[82px] h-[24px]"
			>
				Webview
			</div>
		</div>
		<div v-else>
			<div class="flex flex-row items-center space-x-2">
				<div
					class="bg-white rounded-md shadow px-2 py-0.5 w-[82px] h-[24px] group"
				>
					<div>{{ selectedList }}</div>
					<div
						class="group-hover:visible invisible rounded-b-md ml-[-8px] mt-[-3px] w-[82px] shadow absolute z-50 bg-white"
					>
						<div class="flex flex-col text-base py-0.5 px-1">
							<div
								class="hover:bg-gray-100 rounded cursor-pointer py-0.5 px-1"
								@click="
									() => {
										selectedList =
											selectedList === 'Articles'
												? 'Categories'
												: 'Articles'
										$router.push({
											path: `/frappedesk/knowledge-base/${selectedList.toLowerCase()}`,
										})
									}
								"
							>
								{{
									selectedList === "Articles"
										? "Categories"
										: "Articles"
								}}
							</div>
						</div>
					</div>
				</div>
				<router-link
					:title="'Toggle Web view'"
					:to="{ path: '/frappedesk/knowledge-base' }"
				>
					<FeatherIcon
						role="button"
						name="layout"
						class="h-5 w-5 mr-2 stroke-gray-500 hover:stroke-gray-900"
					/>
				</router-link>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"

export default {
	name: "LayoutSwitcher",
	props: {
		viewMode: {
			type: String,
			default: "Web",
		},
		selectedList: {
			type: String,
			default: "Articles", // Articles, Categories
		},
	},
	components: {
		FeatherIcon,
	},
	setup(props) {
		console.log(props.selectedList)
	},
}
</script>
