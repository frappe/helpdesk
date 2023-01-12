<template>
	<LoginBox
		v-if="!signupStatus"
		:title="this.$route.name === 'PortalSignup' ? 'Create an account' : ''"
	>
		<div v-if="this.$route.name === 'PortalSignup'">
			<form class="space-y-4" @submit.prevent="signup()">
				<Input
					label="Email"
					type="email"
					placeholder="johndoe@mail.com"
					autocomplete="email"
					v-model="email"
					required
				/>
				<Input
					label="First Name"
					type="text"
					placeholder="John"
					v-model="firstName"
					class="mb-4"
					required
				/>
				<Input
					label="Last Name"
					type="text"
					placeholder="Doe"
					v-model="lastName"
					class="mb-4"
					required
				/>
				<ErrorMessage class="mt-4" error="" />
				<div>
					<Button
						appearance="primary"
						class="w-full mt-4"
						:loading="submitting"
						type="primary"
					>
						Submit
					</Button>
				</div>
				<div>
					<div class="mt-10 border-t text-center">
						<div class="-translate-y-1/2 transform">
							<span
								class="bg-white px-2 text-xs uppercase leading-8 tracking-wider text-gray-800"
							>
								Or
							</span>
						</div>
					</div>
				</div>
				<router-link
					class="text-center text-base"
					:to="`${
						this.$route.name === 'DeskSignup'
							? '/helpdesk'
							: '/support'
					}/login`"
				>
					<div>Already have an account? Log in.</div>
				</router-link>
			</form>
		</div>
		<div v-else class="text-base mt-[-20px]">
			<div class="flex space-x-3">
				<FeatherIcon
					name="alert-triangle"
					class="h-10 w-10 stroke-2 stroke-orange-500"
				/>
				<div>Please ask the admin to add you as an agent</div>
			</div>
		</div>
	</LoginBox>
	<SuccessCard
		class="mx-auto mt-20 w-96 shadow-md"
		title="Verification Email Sent!"
		v-else-if="signupStatus === 'EMAIL SENT'"
	>
		We have sent an email to <span class="font-semibold">{{ email }}</span
		>. Please click on the link received to verify your email and set up
		your account.
	</SuccessCard>
	<ErrorCard
		class="mx-auto mt-20 w-96 shadow-md"
		title="Error while signing up!"
		v-else
	>
		<div class="flex flex-col space-y-5">
			<div>
				{{ error }}
			</div>
			<div>
				<Button appearance="primary" @click="$router.go()"
					>Try Again</Button
				>
			</div>
		</div>
	</ErrorCard>
</template>

<script>
import LoginBox from "@/components/global/LoginBox.vue"
import { Input, FeatherIcon, ErrorMessage } from "frappe-ui"
import SuccessCard from "@/components/global/SuccessCard.vue"
import ErrorCard from "@/components/global/ErrorCard.vue"
import { ref, inject } from "vue"

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
		const email = ref(null)
		const firstName = ref(null)
		const lastName = ref(null)

		const signupStatus = ref(null)
		const error = ref(null)

		const user = inject("user")

		const submitting = ref(false)

		return {
			email,
			firstName,
			lastName,
			signupStatus,
			user,
			submitting,
			error,
		}
	},
	async mounted() {
		if (this.user.isLoggedIn()) {
			if (this.$route.name == "PortalSignup") {
				this.$router.push({ path: "/support/tickets" })
			} else if (this.$route.name == "DeskSignup") {
				this.$router.push({ path: "/helpdesk/tickets" })
			}
		}
	},
	methods: {
		async signup() {
			this.submitting = true

			this.$event.on("user-signup-success", (res) => {
				this.submitting = false
				this.signupStatus = "EMAIL SENT"
			})
			this.$event.on("user-signup-error", (error) => {
				this.error = error
				this.submitting = false
				this.signupStatus = "SINGUP ERROR"
			})

			await this.user.signup(this.email, this.firstName, this.lastName)

			this.$event.off("user-signup-success")
			this.$event.off("user-signup-error")
		},
	},
}
</script>
