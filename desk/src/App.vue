<template>
  <div>
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  provide: {
		viewportWidth: Math.max(
			document.documentElement.clientWidth || 0,
			window.innerWidth || 0
		)
	}
}
</script>