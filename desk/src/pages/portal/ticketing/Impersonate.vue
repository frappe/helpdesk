<template>
	<div class="mt-5">
		<LoadingText text="Impersonating contact..." />
	</div>
</template>

<script>
import { inject, ref } from "@vue/runtime-core"
import { LoadingText } from "frappe-ui"

export default {
	name: "Impersonate",
	components: {
		LoadingText,
	},
	setup() {
		const contact = ref("")
		const ticketId = ref("")
		const impersonateContact = inject("impersonateContact")

		return { contact, ticketId, impersonateContact }
	},
	watch: {
		async impersonateContact(impersonateContact) {
			if (impersonateContact) {
				if (this.$route.query) {
					this.contact = this.$route.query["contact"]
					this.ticketId = this.$route.query["ticketId"]
				}
				await impersonateContact(this.contact)
				this.ticketId
					? this.$router.push({
							path: `/helpdesk/my-tickets/${this.ticketId}`,
					  })
					: this.$router.push({ path: "/helpdesk/my-tickets" })
			}
		},
	},
}
</script>
