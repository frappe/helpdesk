import { useClipboard } from "@vueuse/core";
import { createToast } from "./toasts";

export async function copy(s: string) {
  const { copy: c } = useClipboard();
  c(s).then(() =>
    createToast({
      title: "Copied to clipboard",
      icon: "check",
      iconClasses: "text-green-600",
    })
  );
}
