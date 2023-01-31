<template>
	<div class="flex flex-col max-h-screen">
		<div class="flex border-b h-[52px] px-6 shrink-0">
			<div class="grow my-auto">
				<BaseBreadcrumbs
					:breadcrumbs="[
						{
							label: 'Customers',
							name: 'customer',
							handler: () => {
								$router.push({
									path: `/frappedesk/customers`,
								})
							},
						},
						{
							label: `${customerId}`,
							name: 'customerId',
						},
					]"
				/>
			</div>
		</div>
		<div class="customer max-h-[calc(100vh-52px)]">
			<CustomerInfo
				class="flex border-r border-gray-100 w-full"
				:customer="customerId"
			/>
		</div>
	</div>
</template>

<script>
import CustomerInfo from "@/components/desk/customers/CustomerInfo.vue"
import BaseBreadcrumbs from "@/components/global/BaseBreadcrumbs.vue"
export default {
	name: "Customer",
	props: ["customerId"],
	components: {
		CustomerInfo,
		BaseBreadcrumbs,
	},
}
</script>
