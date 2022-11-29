<template>
	<div class="flex flex-col">
		<div class="flex border-b h-[52px] px-[24px] shrink-0">
			<div class="grow my-auto text-[16px] font-semibold text-gray-900">
				Customers
			</div>
		</div>
		<div class="customer">
			<CustomerInfo
				class="flex border-r border-[#F4F5F6] w-full"
				:customer="customerId"
			/>
		</div>
	</div>
</template>

<script>
import CustomerInfo from "@/components/desk/customers/CustomerInfo.vue"
export default {
	name: "Customer",
	props: ["customerId"],
	components: {
		CustomerInfo,
	},
}
</script>
