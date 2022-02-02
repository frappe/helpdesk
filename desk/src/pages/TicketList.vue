<template>
	<div>
		<div class="sm:py-1 sm:border sm:border-gray-100 sm:rounded-md sm:shadow sm:px-2">
			<div class="block py-2 rounded-md sm:px-2">
				<div class="block py-2 rounded-md sm:px-2">
					<div class="flex items-center justify-between sm:justify-start font-bold">
						<div class="mr-4">
							<Input type="checkbox" value="" />
						</div>
						<div class="text-base sm:w-7/12">
							Subject
						</div>
						<div class="text-base sm:w-3/12">
							Requester
						</div> 
						<div class="text-base sm:w-1/12">
							Status
						</div> 
						<div class="text-base sm:w-1/12">
							Modified
						</div> 
					</div>
				</div>
				<div class="pt-2 transform translate-y-2 border-b-4"/>
			</div>
			<div 
				class="w-full block overflow-auto"
        		:style="{ height: viewportWidth > 768 ? 'calc(100vh - 15rem)' : null }"
			>
				<div class="flex-auto" v-for="ticket in tickets" :key="ticket.name">
					<div class="block rounded-md sm:px-2">
						<a :href="ticket.name" class="block py-2 rounded-md sm:px-2 hover:bg-gray-50">
							<div class="flex items-center justify-between sm:justify-start">
								<div class="mr-4">
									<Input type="checkbox" value="" />
								</div>
								<div class="text-base sm:w-7/12">
									{{ ticket.subject }}
								</div>
								<div class="text-base sm:w-3/12">
									{{ ticket.contact }}
								</div> 
								<div class="text-base sm:w-1/12">
									<span class="inline-block px-3 py-1 text-xs font-medium rounded-md cursor-default pointer-events-none text-gray-700 bg-gray-50">
										{{ ticket.status }}
									</span>
								</div> 
								<div class="hidden w-1/12 text-sm text-gray-600 sm:block">
									{{ ticket.modified }}
								</div> 
							</div>
							<div class="pt-2 transform translate-y-2 border-b"/>
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from 'frappe-ui'

export default {
	name: 'TicketList',
	props: ['tickets'],
	inject: ['viewportWidth'],
	components: {
		Input
	},
}
</script>
