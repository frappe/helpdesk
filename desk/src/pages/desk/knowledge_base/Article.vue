<template>
	<div>
		<div>
			{{ article.title }}
		</div>
		<div>
			{{ article.content }}
		</div>
	</div>
</template>

<script>
export default {
	name: 'Article',
	props: ['articleId'],
	computed: {
		isNew() {
			return this.articleId ? false : true
		},
		article() {
			if (!this.isNew) {
				return this.$resources.article.doc || {}
			} 
			
			return {}
		}
	},
	mounted() {
		this.$event.emit('toggle_navbar_actions', 'Article')
	},
	resources: {
		article() {
			if (!this.isNew) {
				return {
					type: 'document',
					doctype: 'Article',
					name: this.articleId
				}
			} else {
				return false
			}
		}
	}
}
</script>

<style>

</style>