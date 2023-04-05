<template>
	<LoginBox title="Account Setup">
		<form class="space-y-4" @submit.prevent="verifyAccount()">
			<Input
				label="Email"
				type="email"
				placeholder="johndoe@mail.com"
				autocomplete="email"
				v-model="email"
				required
			/>
			<Input
				label="Password"
				type="password"
				placeholder="*****"
				v-model="password"
				required
			/>
			<ErrorMessage class="mt-4" error="" />
			<div>
				<Button
					appearance="primary"
					class="w-full mt-4"
					:loading="false"
					type="primary"
				>
					Submit
				</Button>
			</div>
		</form>
	</LoginBox>
</template>

<script>
import LoginBox from "../../components/global/LoginBox.vue"
import { Input } from "frappe-ui"
import { ref, inject } from "vue"
import { useAuthStore } from "@/stores/auth"

export default {
	name: "VerifyAccount",
	props: ["requestKey"],
	components: {
		LoginBox,
		Input,
	},
	setup() {
		const authStore = useAuthStore();
		const email = ref("")
		const password = ref("")

		return { authStore, email, password }
	},
	resources: {
		verifyAccount() {
			return {
				url: "helpdesk.api.account.verify_and_create_account",
				onSuccess: async () => {
					await this.authStore.login(this.email, this.password)
					this.$router.push("/my-tickets")
				},
				onError: () => {},
			}
		},
	},
	methods: {
		verifyAccount() {
			this.$resources.verifyAccount.submit({
				request_key: this.requestKey,
				email: this.email,
				password: this.password,
			})
		},
	},
}
</script>

<style></style>
