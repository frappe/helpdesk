<template>
	<div class="bg-[#F3F5F8] h-screen w-screen">
		<div class="p-[80px]">
			<div
				class="bg-white rounded-[10px]"
				style="{
					box-shadow: 0px 1px 42px rgba(97, 97, 97, 0.07);
					height: calc(100vh - 160px);
				}"
			>
				<div class="py-[60px] flex justify-center">
					<div class="flex flex-col space-y-[60px] max-w-[370px]">
						<div class="flex justify-center">
							<CustomIcons name="frappedesk" class="h-[24px]"/>
						</div>
						<div>
							<form v-if="currentStep == 1" @submit.prevent="submitStep">
								<div class="text-[24px] font-bold mb-[10px] text-gray-900">
									Welcome to FrappeDesk
								</div>
								<div class="text-[16px] font-normal text-gray-600 mb-[30px]">
									Thanks for verifying your e-mail.
								</div>
								<div class="text-[16px] font-normal text-gray-900 mb-[30px]">
									Configure your e-mail address to start sending and receiving e-mails into FrappeDesk.
								</div>
								 <label class="flex flex-col space-y-[10px] mb-[30px]">
									<span class="block mb-2 text-sm leading-4 text-gray-700">
										E-mail ID
									</span>
									<input type="text" class="rounded-[6px] w-full border-[#EBEEF0] h-[36px]" />
								</label>
								<label class="flex flex-col space-y-[10px] mb-[30px]">
									<span class="block mb-2 text-sm leading-4 text-gray-700">
										Password
									</span>
									<input type="password" class="rounded-[6px] w-full border-[#EBEEF0] h-[36px]" />
								</label>
								<Button appearance="primary" class="w-full mb-[14px]">Next</Button>
								<div class="flex justify-center">
									<div 
										class="text-base font-normal text-gray-600 text-center hover:text-gray-700"
										role="button"
										@click="skip"
									>
										Skip
									</div>
								</div>
							</form>
							<form v-if="currentStep == 2" @submit.prevent="submitStep">
								<div class="text-[24px] font-bold mb-[30px] text-gray-900">
									Let’s invite your teammates
								</div>
								 <label class="flex flex-col space-y-[10px] mb-[30px]">
									<span class="block mb-2 text-sm leading-4 text-gray-700">
										E-mail IDs (comma-separated)
									</span>
									<textarea rows="3" class="max-h-[130px] min-h-[80px] placeholder-gray-400 text-[16px] font-normal rounded-[6px] w-full border-[#EBEEF0]" placeholder="tom@frappe.io, alex@frappe.io, joe@frappe.io" />
								</label>
								<Button appearance="primary" class="w-full mb-[14px]">Finish</Button>
								<div class="flex justify-center mb-[30px]">
									<div class="text-base font-normal text-gray-600 text-center hover:text-gray-700" role="button">I’ll do this later</div>
								</div>
								<div 
									class="max-w-fit text-base font-normal text-gray-600 hover:text-gray-700" 
									role="button" 
									@click="goBack"
								>
									← Back
								</div>
							</form>
						</div>
					</div>
				</div>
			</div>	
		</div>
	</div>
</template>

<style scoped>
	.form-input {
		background: white !important;
	}
</style>

<script>
import CustomIcons from '@/components/desk/global/CustomIcons.vue';
import { ref } from 'vue'

export default {
    name: "DeskSetup",
    components: {
		CustomIcons
	},
	setup() {
		const currentStep = ref(1)
		const totalSteps = ref(2)

		return {
			currentStep,
			totalSteps,
		}
	},
	methods: {
		submitStep() {
			if (this.currentStep < this.totalSteps) {
				this.currentStep++
			} else {
				console.log('setup completed')
			}
		},
		skip() {
			this.currentStep++
		},
		goBack() {
			if (this.currentStep > 1) {
				this.currentStep--
			}
		}
	}
}
</script>

<style>

</style>