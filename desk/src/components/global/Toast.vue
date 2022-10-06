<template>
	<teleport to="#frappeui-toast-root">
		<transition
			:name="position.includes('top') ? 'toast-top' : 'toast-bottom'"
		>
			<div
				v-if="shown"
				:style="style"
				:class="[
					'absolute transition duration-200 ease-out mx-[15px] pointer-events-auto',
					position.includes('center') ? '-translate-x-1/2' : '',
					position.includes('top') ? 'my-[80px]' : 'my-[10px]',
				]"
			>
				<div
					class="px-5 pt-[14px] pb-[12px] rounded-lg shadow-md min-w-[25rem] max-w-[40rem] flex flex-col space-y-5"
					:class="bodyClasses"
				>
					<div class="flex items-start">
						<div
							v-if="icon || customIcon"
							class="grid w-5 h-5 mr-3 place-items-center"
						>
							<FeatherIcon
								v-if="icon"
								:name="icon"
								:class="['w-5 h-5', iconClasses]"
							/>
							<CustomIcons
								v-else
								:name="customIcon"
								:class="['w-5 h-5', iconClasses]"
							/>
						</div>
						<div class="w-full">
							<slot>
								<p
									class="text-[14px] font-medium text-gray-900"
								>
									{{ title }}
								</p>
								<p
									class="mt-1 text-base font-normal text-gray-700"
								>
									{{ text }}
								</p>
								<form
									v-if="form"
									class="mt-2"
									@submit.prevent="
										() => {
											$clearToasts()
											form.submit
												? form.submit.action(formInputs)
												: form.onSubmit(formInputs)
										}
									"
								>
									<div
										class="flex flex-col space-y-3 mb-3"
										v-for="input in form.inputs"
										:key="input.fieldname"
									>
										<Input
											class="rounded-lg bg-white"
											:type="
												input.type ? input.type : 'text'
											"
											:placeholder="input.placeholder"
											@input="
												(val) => {
													formInputs[
														input.fieldname
													] = val
												}
											"
										/>
									</div>
								</form>
								<div class="flex mt-5" v-if="action || form">
									<Button
										appearance="primary"
										@click="
											() => {
												$clearToasts()
												if (form) {
													form.submit
														? form.submit.action(
																formInputs
														  )
														: form.onSubmit(
																formInputs
														  )
												} else {
													if (
														typeof action ===
														'function'
													) {
														action()
													} else {
														action.onClick()
													}
												}
											}
										"
										>{{
											action
												? action.title
												: form.submit
												? form.submit.title
												: "Submit"
										}}</Button
									>
								</div>
							</slot>
						</div>
						<div class="pl-2 ml-auto">
							<slot name="actions">
								<div
									role="button"
									class="grid w-5 h-5 place-items-center"
									@click="
										() => {
											shown = false
											onClose()
										}
									"
								>
									<FeatherIcon
										name="x"
										class="w-4 h-4 stroke-2"
										:class="closeIconClassess"
									/>
								</div>
							</slot>
						</div>
					</div>
				</div>
			</div>
		</transition>
	</teleport>
</template>
<script>
import { FeatherIcon } from "frappe-ui"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "Toast",
	props: {
		position: {
			type: String,
			default: "top-right",
		},
		icon: {
			type: String,
		},
		customIcon: {
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
		form: {
			type: Object,
			default: null,
		},
		appearance: {
			type: String,
		},
		timeout: {
			type: Number,
			default: 5,
		},
		fixed: {
			type: Boolean,
			default: false,
		},
		action: {
			type: Object,
			default: null,
		},
		onClose: {
			type: Function,
			default: () => {},
		},
	},
	components: {
		FeatherIcon,
		CustomIcons,
	},
	created() {
		if (!document.getElementById("frappeui-toast-root")) {
			const root = document.createElement("div")
			root.id = "frappeui-toast-root"
			root.style.position = "fixed"
			root.style.top = "16px"
			root.style.right = "16px"
			root.style.bottom = "16px"
			root.style.left = "16px"
			root.style.zIndex = "9999"
			root.style.pointerEvents = "none"
			document.body.appendChild(root)
		}
	},
	mounted() {
		this.shown = true
		if (!this.fixed) {
			setTimeout(() => {
				this.shown = false
			}, this.timeout * 1000)
		}
	},
	data() {
		return {
			shown: false,
			formInputs: {},
		}
	},
	computed: {
		style() {
			let style = {}
			if (this.position.includes("top")) {
				style.top = 0
			}
			if (this.position.includes("bottom")) {
				style.bottom = 0
			}
			if (this.position.includes("right")) {
				style.right = 0
			}
			if (this.position.includes("left")) {
				style.left = 0
			}
			if (this.position.includes("center")) {
				style.left = "50%"
				// style.transform = 'translateX(-50%)'
			}
			return style
		},
		transitionProps() {
			let props = {
				enterActiveClass: "transition duration-200 ease-out",
				enterFromClass: "opacity-0",
				enterToClass: "translate-y-0 opacity-100",
				leaveActiveClass: "transition duration-100 ease-in",
				leaveFromClass: "scale-100 translate-y-0 opacity-100",
				leaveToClass: "scale-75 translate-y-4 opacity-0",
			}
			if (this.position.includes("top")) {
				props.enterFromClass += " -translate-y-12"
			}
			if (this.position.includes("bottom")) {
				props.enterFromClass += " translate-y-12"
			}
			return props
		},
		bodyClasses() {
			if (this.appearanceColor === "white") return "bg-white"
			return `bg-${this.appearanceColor}-${
				this.appearanceColor === "red" ? "100" : "50"
			}`
		},
		closeIconClassess() {
			return `stroke-${this.appearanceColor}-600`
		},
		appearanceColor() {
			let color = "white"
			if (this.appearance) {
				switch (this.appearance) {
					case "danger":
						color = "red"
						break
					case "success":
						color = "green"
						break
					case "warning":
						color = "yellow"
						break
					case "info":
						color = "blue"
						break
					default:
						color = "white"
						break
				}
			}
			return color
		},
	},
}
</script>
<style>
.toast-top-enter-active,
.toast-bottom-enter-active {
	transition: all 200ms ease-out;
}
.toast-top-leave-active,
.toast-bottom-leave-active {
	transition: all 100ms ease-in;
}
.toast-top-enter-from {
	opacity: 0;
	transform: translateY(0);
}
.toast-top-enter-to {
	opacity: 1;
	transform: translateY(0);
}
</style>
