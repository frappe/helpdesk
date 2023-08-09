import { createToast } from "@/utils/toasts";

interface Options {
  title?: string;
  icon?: string;
  iconClass?: string;
}

interface Error {
  message?: string;
  messages?: string[];
}

export function useError(o?: Options) {
  function getMessage(e: Error) {
    if (e.message) return e.message;
    return e.messages.join(", ");
  }

  function getTitle(e: Error) {
    if (o?.title) return o?.title;
    return getMessage(e);
  }

  function getFunc() {
    return function (e: Error) {
      createToast({
        title: getTitle(e),
        message: o?.title ? undefined : getMessage(e),
        icon: o?.icon ?? "x",
        iconClass: o?.iconClass ?? "text-red-500",
      });
    };
  }

  return {
    getFunc,
    getMessage,
    getTitle,
  };
}
