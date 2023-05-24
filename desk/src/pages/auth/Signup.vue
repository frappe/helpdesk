<template>
	<LoginBox v-if="!signupStatus" title="Create an account">
		<div v-if="$route.name === 'Signup'">
			<form class="space-y-4" @submit.prevent="signup()">
				<Input
					v-model="email"
					type="email"
					placeholder="john.doe@example.com"
					label="Email"
					autocomplete="email"
					required
				/>
				<Input
					v-model="firstName"
					type="text"
					label="Firstname"
					placeholder="John"
					required
				/>
				<Input
					v-model="lastName"
					type="text"
					label="Lastname"
					placeholder="Doe"
					required
				/>
				<div>
					<Button
						class="w-full bg-gray-900 text-white hover:bg-gray-800"
						label="Signup"
						:loading="submitting"
						type="primary"
					/>
				</div>
				<div>
					<div class="mt-10 border-t text-center">
						<div class="-translate-y-1/2">
							<span class="bg-white px-2 text-xs tracking-wider text-gray-700">
								OR
							</span>
						</div>
					</div>
				</div>
				<router-link class="text-center text-base" :to="{ name: 'Login' }">
					<div>Already have an account? Login</div>
				</router-link>
			</form>
		</div>
		<div v-else class="mt-[-20px] text-base">
			<div class="flex space-x-3">
				<FeatherIcon
					name="alert-triangle"
					class="h-10 w-10 stroke-orange-500 stroke-2"
				/>
				<div>Please ask the admin to add you as an agent</div>
			</div>
		</div>
	</LoginBox>
	<SuccessCard
		v-else-if="signupStatus === 'EMAIL SENT'"
		class="mx-auto mt-20 w-96 shadow-md"
		title="Verification Email Sent!"
	>
		We have sent an email to <span class="font-semibold">{{ email }}</span
		>. Please click on the link received to verify your email and set up your
		account.
	</SuccessCard>
	<ErrorCard
		v-else
		class="mx-auto mt-20 w-96 shadow-md"
		title="Error while signing up!"
	>
		<div class="flex flex-col space-y-5">
			<div>
				{{ error }}
			</div>
			<div>
				<Button appearance="primary" @click="$router.go()">Try Again</Button>
			</div>
		</div>
	</ErrorCard>
</template>

<script>
import LoginBox from "@/components/global/LoginBox.vue";
import { Input, FeatherIcon, ErrorMessage } from "frappe-ui";
import SuccessCard from "@/components/global/SuccessCard.vue";
import ErrorCard from "@/components/global/ErrorCard.vue";
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";

export default {
	name: "Signup",
	components: {
		LoginBox,
		Input,
		FeatherIcon,
		ErrorMessage,
		SuccessCard,
		ErrorCard,
	},
	setup() {
		const authStore = useAuthStore();
		const email = ref(null);
		const firstName = ref(null);
		const lastName = ref(null);
		const signupStatus = ref(null);
		const error = ref(null);
		const submitting = ref(false);

		return {
			authStore,
			email,
			firstName,
			lastName,
			signupStatus,
			submitting,
			error,
		};
	},
	mounted() {
		if (this.authStore.isLoggedIn) {
			this.$router.push({ name: "WebsiteRoot" });
		}
	},
	methods: {
		async signup() {
			this.submitting = true;

			await this.authStore
				.signup(this.email, this.firstName, this.lastName)
				.then(() => (this.signupStatus = "EMAIL SENT"))
				.catch((error) => {
					this.signupStatus = "SIGNUP ERROR";
					this.error = error.messages.join("\n");
				})
				.finally(() => (this.submitting = false));
		},
	},
};
</script>
