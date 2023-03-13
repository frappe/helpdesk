<template>
	<div
		class="my-2 min-w-[15rem] max-w-[40rem] rounded-lg border bg-white p-4 shadow-md"
	>
		<div class="flex items-start">
			<div v-if="icon" class="mr-3 grid h-5 w-5 place-items-center">
				<FeatherIcon :name="icon" :class="['h-5 w-5', iconClasses]" />
			</div>
			<div>
				<slot>
					<p
						v-if="title"
						class="text-base font-medium text-gray-900"
						:class="{ 'mb-1': text }"
					>
						{{ title }}
					</p>
					<p v-if="text" class="text-base text-gray-600">
						{{ text }}
					</p>
					<div class="flex flex-wrap gap-1 pt-2">
						<Button
							v-for="b in buttons"
							:appearance="b.appearance"
							:icon-left="b.iconLeft"
							:icon-right="b.iconRight"
							@click="b.onClick"
						>
							{{ b.title }}
						</Button>
					</div>
					<div v-if="form">
						<form
							:class="form.classes"
							@submit.prevent="(event) => submitForm(form, event)"
						>
							<Input
								v-for="input in form.inputs"
								:type="input.type"
								:placeholder="input.placeholder"
								:name="input.fieldname"
							/>
							<Button appearance="primary" value="submit">Submit</Button>
						</form>
					</div>
				</slot>
			</div>
			<div class="ml-auto pl-2">
				<slot name="actions">
					<button
						class="grid h-5 w-5 place-items-center rounded hover:bg-gray-100"
						@click="onToastClose"
					>
						<FeatherIcon name="x" class="h-4 w-4 text-gray-700" />
					</button>
				</slot>
			</div>
		</div>
	</div>
</template>
<script>
import { FeatherIcon } from "frappe-ui";
const positions = [
	"top-right",
	"top-center",
	"top-left",
	"bottom-right",
	"bottom-center",
	"bottom-left",
];

export default {
	name: "Toast",
	components: {
		FeatherIcon,
	},
	props: {
		position: {
			type: String,
			default: "top-center",
		},
		icon: {
			type: String,
		},
		iconClasses: {
			type: String,
		},
		title: {
			type: String,
		},
		text: {
			type: String,
		},
		timeout: {
			type: Number,
			default: 5,
		},
		buttons: {
			type: Array,
			default: [],
		},
		form: {
			type: Object,
		},
		actionOnClose: {
			type: Function,
		}
	},
	emits: ["close"],
	mounted() {
		if (this.timeout > 0) {
			setTimeout(this.onToastClose, this.timeout * 1000);
		}
	},
	methods: {
		onToastClose() {
			if (this.actionOnClose instanceof Function) this.actionOnClose();
			this.$emit('close');
		},
		submitForm(form, event) {
			if (form.onSubmit instanceof Function) form.onSubmit(event);
			this.$emit("close");
		},
	},
};
</script>
