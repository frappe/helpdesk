<template>
	<LoginBox
		v-if="!successMessage"
		:title="!forgot ? 'Log in to your account' : 'Reset your password'"
	>
		<form class="space-y-4" @submit.prevent="login">
			<Input label="Username" type="text" v-model="email" placeholder="johndeo@gmail.com" />
			<Input label="Password" type="password" v-model="password" placeholder="" />
			<div class="mt-2 text-sm">
				<router-link v-if="forgot" to="/login">
					I remember my password
				</router-link>
				<router-link v-else to="/login/forgot"> Forgot Password </router-link>
			</div>
			<ErrorMessage :error="errorMessage" class="mt-4" />
			<Button
				appearance="primary"
				class="w-full"
				:disabled="state === 'RequestStarted'"
				@click="loginOrResetPassword"
				type="primary"
			>
				Submit
			</Button>
			<div>
				<template v-if="!forgot">
					<div class="mt-10 border-t text-center">
						<div class="-translate-y-1/2 transform">
							<span
								class="bg-white px-2 text-xs uppercase leading-8 tracking-wider text-gray-800"
							>
								Or
							</span>
						</div>
					</div>
					<router-link to="/signup">
						<div class="text-center text-base">
							Sign up for a new account
						</div>
					</router-link>
				</template>
			</div>
		</form>
	</LoginBox>
	<SuccessCard v-else class="mx-auto mt-20" title="Password Reset Link Sent.">
		We have sent an email to <span class="font-semibold">{{ email }}</span
		>. Please click on the link received to reset your password.
	</SuccessCard>
</template>

<script>
import LoginBox from "@/components/global/LoginBox.vue";
import { Input } from 'frappe-ui'
import { ref, inject } from 'vue';

export default {
	name: "Login",
	props: {
		forgot: {
			default: false
		}
	},
	components: {
		LoginBox,
		Input
	},
	setup() {
		const state = ref(null) // Idle, Logging In, Login Error
		const email =  ref(null)
		const password =  ref(null)
		const errorMessage =  ref(null)
		const successMessage =  ref(null)
		const redirect_route =  ref(null)

		const user = inject('user')

		return { state, email, password, errorMessage, successMessage, redirect_route, user }
	},
	watch: {
		forgot() {
			this.errorMessage = null;
			this.state = null;
			this.password = null;
			this.successMessage = null;
		}
	},
	async mounted() {
		if (this.$route?.query?.route) {
			this.redirect_route = this.$route.query.route;
			this.$router.replace({ query: null });
		}
	},
	methods: {
		async loginOrResetPassword() {
			console.log('submit button clicked!!!')
			try {
				this.errorMessage = null;
				this.state = 'RequestStarted';
				if (!this.forgot) {
					await this.login();
				} else {
					console.log('here')
					await this.resetPassword();
				}
			} catch (error) {
				console.error(error)
				this.errorMessage = error.messages.join('\n');
			} finally {
				this.state = null;
			}
		},
		async login() {
			console.log(this.email, this.password)
			if (this.email && this.password) {
				let res = await this.user.login(this.email, this.password);
				if (res) {
					this.$router.push(this.redirect_route || res.dashboard_route || '/');
				}
			}
		},
		async resetPassword() {
			await this.user.resetPassword(this.email);
			this.successMessage = true;
		}
	}
}
</script>

<style>

</style>