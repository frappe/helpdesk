import { createToast } from './toasts';

export const clipboardCopy = (s: string) => {
	// https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText
	window
		.navigator
		.clipboard
		.writeText(s)
		.then(() => {
			createToast({
				title: "Copied to clipboard",
				icon: "check",
				iconClasses: "text-green-500",
			});
		})
		.catch(() => {
			createToast({
				title: "Error copying to clipboard",
				icon: "x",
				iconClasses: "text-red-500",
			});
		});
}
