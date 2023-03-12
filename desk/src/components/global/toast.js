import { h, reactive, TransitionGroup, ref, Teleport } from "vue";
import Toast from "./Toast.vue";

let toasts = ref([]);

export let Toasts = {
	name: "Toasts",
	created() {
		if (typeof window === "undefined") return;
		if (!document.getElementById("frappeui-toast-root")) {
			const root = document.createElement("div");
			root.id = "frappeui-toast-root";
			root.style.position = "fixed";
			root.style.top = "16px";
			root.style.right = "16px";
			root.style.bottom = "16px";
			root.style.left = "16px";
			root.style.zIndex = "9999";
			root.style.pointerEvents = "none";
			document.body.appendChild(root);
		}
	},
	render() {
		return h(Teleport, { to: "#frappeui-toast-root" }, [
			getToastsGroup("top-left"),
			getToastsGroup("top-center"),
			getToastsGroup("top-right"),
			getToastsGroup("bottom-left"),
			getToastsGroup("bottom-center"),
			getToastsGroup("bottom-right"),
		]);
	},
};

function getToastsGroup(position) {
	let transition =
		"transition duration-[230ms] ease-[cubic-bezier(.21,1.02,.73,1)]";
	let classes = ["absolute"];
	if (position === "top-left") {
		classes.push("top-0 left-0");
	}
	if (position === "top-right") {
		classes.push("top-0 right-0");
	}
	if (position === "top-center") {
		classes.push("top-0 left-1/2 -translate-x-1/2");
	}
	if (position === "bottom-left") {
		classes.push("bottom-0 left-0");
	}
	if (position === "bottom-right") {
		classes.push("bottom-0 right-0");
	}
	if (position === "bottom-center") {
		classes.push("bottom-0 left-1/2 -translate-x-1/2");
	}

	return h(
		TransitionGroup,
		{
			tag: "div",
			class: classes,
			moveClass: transition,
			enterActiveClass: transition,
			enterFromClass: "translate-y-1 opacity-0",
			enterToClass: "translate-y-0 opacity-100",
			leaveActiveClass: `${transition} absolute`,
			leaveFromClass: "translate-y-0 opacity-100",
			leaveToClass: "translate-y-1 opacity-0",
		},
		() =>
			toasts.value
				.filter((toast) => toast.position === position)
				.map((toast) => {
					return h(
						"div",
						{ key: toast.key, class: "pointer-events-auto flex" },
						h(Toast, {
							...toast,
							onClose: () => {
								toasts.value = toasts.value.filter((t) => t !== toast);
							},
						})
					);
				})
	);
}

export function toast(options) {
	let id = `toast-${Math.random().toString(36).slice(2, 9)}`;
	let toast = reactive({
		key: id,
		position: "top-center",
		...options,
	});
	toasts.value.push(toast);
	return id;
}
