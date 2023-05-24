<template>
	<LoginBox v-if="!successMessage" title="Login to your account">
		<form class="space-y-4" @submit.prevent="login">
			<Input
				v-model="email"
				required
				:type="email !== 'Administrator' ? 'email' : 'text'"
				label="Email"
				placeholder="john.doe@example.com"
			/>
			<Input
				v-model="password"
				type="password"
				placeholder="••••••••"
				label="Password"
				name="password"
				autocomplete="current-password"
				required
			/>
			<ErrorMessage :message="errorMessage" />
			<Button
				class="w-full bg-gray-900 text-white hover:bg-gray-800"
				label="Login"
				:disabled="state === 'RequestStarted'"
				type="primary"
				@click="login"
			/>
			<div>
				<div class="mt-8 border-t text-center">
					<div class="-translate-y-1/2">
						<span class="bg-white px-2 text-xs tracking-wider text-gray-700">
							OR
						</span>
					</div>
				</div>
				<router-link
					class="text-center text-base"
					:to="`${$route.name === 'DeskLogin' ? '' : ''}/signup`"
				>
					<div>Sign up for a new account</div>
				</router-link>
			</div>
		</form>
	</LoginBox>
	<SuccessCard v-else class="mx-auto mt-20" title="Password Reset Link Sent.">
		We have sent an email to <span class="font-semibold">{{ email }}</span
		>. Please click on the link received to reset your password.
	</SuccessCard>
</template>

<script>
import { ref } from "vue";
import { ErrorMessage, Input } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import LoginBox from "@/components/global/LoginBox.vue";
import SuccessCard from "@/components/global/SuccessCard.vue";

export default {
	name: "Login",
	components: {
		ErrorMessage,
		Input,
		LoginBox,
		SuccessCard,
	},
	setup() {
		const authStore = useAuthStore();
		const state = ref(null); // Idle, Logging In, Login Error
		const email = ref(null);
		const password = ref(null);
		const errorMessage = ref(null);
		const successMessage = ref(null);

		return {
			authStore,
			email,
			errorMessage,
			password,
			state,
			successMessage,
		};
	},
	methods: {
		async login() {
			if (!this.email || !this.password) return;

			this.errorMessage = null;
			this.state = "RequestStarted";

			await this.authStore
				.login(this.email, this.password)
				.catch((error) => (this.errorMessage = error.message))
				.finally(() => (this.state = null));
		},
	},
};
</script>
