<template>
	<div v-if="!user.loading">
		<router-view />
		<Toasts />
	</div>
</template>

<script>
import { provide, ref } from 'vue'
import { call } from 'frappe-ui'
import { Toasts } from '@/utils/toasts'

export default {
	name: "App",
	components: {
		Toasts	
	},
	setup() {
		const user = ref({})
		const viewportWidth = ref(Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0))
		
		provide('user', user)
		provide('viewportWidth', viewportWidth)
		
		return { user }
	},
	mounted() {
		window.addEventListener('online', () => {
			this.$clearToasts()
			this.$toast({
				title: "You're online now",
				icon: 'wifi',
				iconClasses: 'stroke-green-600',
				appearance: 'success',
				position: 'bottom-right'
			})
		})
		window.addEventListener('offline', () => {
			this.$toast({
				title: "You're offline now",
				icon: 'wifi-off',
				iconClasses: 'stroke-red-600',
				appearance: 'danger',
				fixed: true,
				position: 'bottom-right'
			})
		})

		this.user = {
			signup: async (email, firstName, lastName, password) => {
				return await this.$resources.signup.submit({
					email: email,
					first_name: firstName,
					last_name: lastName,
					password: password
				})
			},
			login: async (email, password) => {
				return await this.$resources.login.submit({
					usr: email,
					pwd: password
				})
			},
			logout: async () => {
				await call('logout')
				this.$router.push({path: "/frappedesk/login"})
			},
			resetPassword: async (email) => {
				console.log('reset password')
			},
			isLoggedIn: () => {
				const cookie = Object.fromEntries(
					document.cookie
						.split('; ')
						.map(part => part.split('='))
						.map(d => [d[0], decodeURIComponent(d[1])])
				)

				return cookie.user_id && cookie.user_id !== 'Guest'
			},
			refetch: async (onRefetch = () => {}) => {
				this.user.loading = true
				await this.$resources.user.fetch()
				onRefetch()
			},
			loading: true
		}

		if (this.user.isLoggedIn()) {
			this.$resources.user.fetch()
		} else {
			this.user.loading = false
		}
	},
	resources: {
		user() {
			return {
				method: 'frappedesk.api.agent.get_user',
				onSuccess: () => {
					const userData = this.$resources.user.data
					if (userData) {
						this.user = {...this.user, ...userData}
						this.user.loading = false
					}
				},
				onError: () => {
					// TODO: check if error occured due to not logged in else handle the error
					this.user.loading = false
					this.$router.push({name: "PortalLogin"})
				}
			}
		},
		login() {
			return {
				method: 'login',
				onSuccess: (res) => {
					if (res) {
						this.$router.go()
					}
				},
				onError: (error) => {
					console.error(error)
				}
			};
		},
		signup() {
			return {
				method: 'frappedesk.api.account.signup',
				onSuccess: (res) => {
					this.$event.emit('user-signup-success', res)
				},
				onError: (error) => {
					this.$event.emit('user-signup-error', error)
				}
			}
		},
		helpdeskName() {
			return {
				method: 'frappedesk.api.website.helpdesk_name',
				auto: true,
				onSuccess: (res) => {
					document.title = `FrappeDesk ${res ? ` | ${res}` : ''}`
				}
			}
		}
	}
}
</script>