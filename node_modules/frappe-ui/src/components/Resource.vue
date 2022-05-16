<script>
export default {
  name: 'Resource',
  props: ['options'],
  resources: {
    resource() {
      return this.options
    },
  },
  render() {
    return this.$slots.default({
      resource: this.$resources.resource,
      data: this.$resources.resource.data,
      error: this.$resources.resource.error,
      loading: this.$resources.resource.loading,
      fetch: (params) => this.$resources.resource.fetch(params),
      submit: (params) => this.$resources.resource.submit(params),
    })
  },
}
</script>
