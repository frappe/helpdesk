import { toast } from "../components/global/toast";

export function clearToasts() {
	const root = document.getElementById("frappeui-toast-root");
	if (!root) return;
	root.innerHTML = "";
}

export function createToast(options = {}) {
	toast({
		position: "bottom-right",
		icon: options.customIcon,
		...options,
	});
}
