<template>
	<router-view v-slot="{ Component }">
		<component :is="Component" />
	</router-view>
</template>

<script>
import { provide, ref } from 'vue'
import { call } from 'frappe-ui'

export default {
	name: "App",
	setup() {
		const user = ref({})
		
		provide('user', user)
		
		const viewportWidth = ref(Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0))
		
		provide('viewportWidth', viewportWidth)
		
		return { user }
	},
	mounted() {
		this.user = {
			signup: (fullName, email) => {
				console.log('signup page')
			},
			login: async (email, password) => {
				return await this.$resources.login.submit({
					usr: email,
					pwd: password
				})
			},
			logout: async () => {
				await call('logout')
				window.location.replace("/helpdesk/login");
			},
			resetPassword: async (email) => {
				console.log('reset password')
			},
			showLoginPage: () => {
				// TODO: use frappe build in login redirect with redirect to helpdesk once logged in
				window.location.replace("/helpdesk/login")
			},
			isLoggedIn: () => {
				const cookie = Object.fromEntries(
					document.cookie
						.split('; ')
						.map(part => part.split('='))
						.map(d => [d[0], decodeURIComponent(d[1])])
				)

				return cookie.user_id && cookie.user_id !== 'Guest'
			}
		}

		if (this.user.isLoggedIn()) {
			this.$resources.user.fetch()
		}
	},
	resources: {
		user() {
			return {
				method: 'helpdesk.api.agent.get_user',
				onSuccess: () => {
					const userData = this.$resources.user.data
					if (userData) {
						this.user = {...this.user, ...userData}
					}
				},
				onFailure: () => {
					// TODO: check if error occured due to not logged in else handle the error
					this.user.showLoginPage()
				}
			}
		},
		login() {
			return {
				method: 'login',
				onSuccess: (res) => {
					if (res) {
						this.$resources.user.fetch()
						return res;
					}
				},
				onFailure: (error) => {
					console.log(error)
				}
			};
		}
	}
}
</script>