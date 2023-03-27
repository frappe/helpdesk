<template>
	<div class="py-3 px-20 border-t pt-5 mt-5">
		<div
			class="flex flex-col space-y-2 items-center text-base text-gray-700"
		>
			<div>Did you find this useful?</div>
			<div class="flex flex-row space-x-5">
				<div v-for="option in feedbackOptions" :key="option">
					<div
						@click="
							() => {
								submitFeedback(option.score).then(() => {
									$toast({
										title: 'Thanks for your feedback!',
										customIcon: 'circle-check',
										appearance: 'success',
									})
								})
							}
						"
						class="hover:text-5xl cursor-pointer text-5xl hover:saturate-100"
						style="color: #855223"
						:class="
							feedback !== null
								? feedback === option.score
									? ''
									: 'saturate-0'
								: 'saturated-100'
						"
					>
						{{ option.emoji }}
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { inject } from "vue"
import { useAuthStore } from "@/stores/auth"

export default {
	name: "ArticleFeedback",
	props: {
		article: {
			type: Object,
			default: null,
		},
	},
	setup() {
		const authStore = useAuthStore()

		return {
			authStore,
		}
	},
	data() {
		return {
			refreshKey: 0,
		}
	},
	computed: {
		feedback() {
			this.refreshKey // used to force re-compute feedback after localstorage update
			if (this.authStore.isLoggedIn) {
				const d = this.$resources.articleFeedback.data || []
				return d.length > 0 ? d[0].feedback : null
			} else {
				// TODO: check local storage if article has a feedback
				return JSON.parse(
					localStorage.getItem(
						`article-${this.article.name}-feedback`
					)
				)
			}
		},
		feedbackOptions() {
			return [
				{
					score: 0,
					emoji: "😞",
				},
				{
					score: 1,
					emoji: "😃",
				},
				// {
				// 	score: 2,
				// 	emoji: "😃",
				// },
			]
		},
	},
	resources: {
		articleFeedback() {
			if (!this.authStore.isLoggedIn) {
				return
			}
			return {
				url: "helpdesk.extends.client.get_list",
				params: {
					doctype: "User Article Feedback",
					filters: {
						article: this.article.name,
						user: this.authStore.userId,
					},
					fields: ["*"],
				},
				auto: true,
			}
		},
		submitArticleFeedback() {
			return {
				url: "helpdesk.api.kb.submit_article_feedback",
				onSuccess: (res) => {
					// TODO: show thank you message
				},
			}
		},
	},
	methods: {
		async submitFeedback(score) {
			// score range: 0 - 1 [0-bad, 1-good]
			if (!this.authStore.isLoggedIn) {
				localStorage.setItem(
					`article-${this.article.name}-feedback`,
					score
				)
			}
			return await this.$resources.submitArticleFeedback
				.submit({
					article: this.article.name,
					score: score,
					previous_score: this.feedback, // will be used in case the user is not signed in
				})
				.then(() => {
					if (this.authStore.isLoggedIn) {
						this.$resources.articleFeedback.fetch()
					} else {
						this.refreshKey += 1
					}
				})
		},
	},
}
</script>
