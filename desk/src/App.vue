<template>
	<router-view v-slot="{ Component }">
		<component :is="Component" />
	</router-view>
</template>

<script>
import { provide, ref } from 'vue'

export default {
	name: "App",
	setup() {
		const user = ref({
			signup: (fullName, email) => {
				console.log('signup page')
			},
			login: (email, password) => {
				console.log('signup page')
			},
			logout: () => {
				console.log('logout user')
			},
			showLoginPage: () => {
				// TODO: use frappe build in login redirect with redirect to helpdesk once logged in
				window.location.replace("/login")
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
		})
		
		provide('user', user)
		
		const viewportWidth = ref(Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0))
		
		provide('viewportWidth', viewportWidth)
		
		return { user }
	},
	mounted() {
		if (this.user.isLoggedIn()) {
			this.$resources.user.fetch()
		} else {
			this.user.showLoginPage()
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
	}
}
</script>