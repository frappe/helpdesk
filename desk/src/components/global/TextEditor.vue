<template>
	<FTextEditor v-bind="$attrs" ref="textEditor">
		<template #top>
			<slot name="top" />
		</template>
		<template #bottom>
			<slot name="bottom" />
		</template>
	</FTextEditor>
</template>
<script>
import { TextEditor as FTextEditor } from "frappe-ui"
export default {
	name: "TextEditor",
	inheritAttrs: false,
	components: { FTextEditor },
}
</script>
