<template>
	<LoginBox
		v-if="!successMessage"
		:title="!forgot ? 'Log in to your account' : 'Reset your password'"
	>
		<form class="space-y-4" @submit.prevent="login">
			<Input
				required
				label="Email"
				:type="email !== 'Administrator' ? 'email' : 'text'"
				v-model="email"
				placeholder="johndeo@gmail.com"
			/>
			<Input
				v-if="!forgot"
				label="Password"
				type="password"
				placeholder="•••••"
				v-model="password"
				name="password"
				autocomplete="current-password"
				required
			/>
			<div class="mt-2 text-sm">
				<router-link v-if="forgot" to="/login">
					I remember my password
				</router-link>
				<router-link v-else to="/login/forgot">
					Forgot Password
				</router-link>
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
					<router-link
						class="text-center text-base"
						:to="`${
							this.$route.name === 'DeskLogin'
								? '/frappedesk'
								: '/support'
						}/signup`"
					>
						<div>Sign up for a new account</div>
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
import LoginBox from "@/components/global/LoginBox.vue"
import { Input } from "frappe-ui"
import { ref, inject } from "vue"

export default {
	name: "Login",
	props: {
		forgot: {
			default: false,
		},
	},
	components: {
		LoginBox,
		Input,
	},
	setup() {
		const state = ref(null) // Idle, Logging In, Login Error
		const email = ref(null)
		const password = ref(null)
		const errorMessage = ref(null)
		const successMessage = ref(null)
		const redirect_route = ref(null)

		const user = inject("user")

		return {
			state,
			email,
			password,
			errorMessage,
			successMessage,
			redirect_route,
			user,
		}
	},
	watch: {
		forgot() {
			this.errorMessage = null
			this.state = null
			this.password = null
			this.successMessage = null
		},
	},
	async mounted() {
		if (this.$route?.query?.route) {
			this.redirect_route = this.$route.query.route
		}
		if (this.user.isLoggedIn()) {
			this.redirect()
		}
	},
	methods: {
		async loginOrResetPassword() {
			try {
				this.errorMessage = null
				this.state = "RequestStarted"
				if (!this.forgot) {
					await this.login()
				} else {
					await this.resetPassword()
				}
			} catch (error) {
				this.errorMessage = error.messages.join("\n")
			} finally {
				this.state = null
			}
		},
		async login() {
			if (this.email && this.password) {
				await this.user.login(this.email, this.password)
				this.redirect()
			}
		},
		async resetPassword() {
			await this.user.resetPassword(this.email)
			this.successMessage = true
		},
		redirect() {
			if (this.redirect_route) {
				window.location.href = this.redirect_route
			} else {
				window.location.href =
					this.$route.name == "DeskLogin"
						? "/frappedesk/tickets"
						: "/support/tickets"
			}
		},
	},
}
</script>

<style></style>
