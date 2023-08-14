import { createToast } from "@/utils";

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
    if (e.messages) return e.messages.join(", ");
    else if (e.message) return e.message;
    else return "";
  }

  function getTitle(e: Error) {
    if (o?.title) return o?.title;
    return getMessage(e);
  }

  return function (e: Error) {
    createToast({
      title: getTitle(e),
      message: o?.title ? undefined : getMessage(e),
      icon: o?.icon ?? "x",
      iconClasses: o?.iconClass ?? "text-red-500",
    });
  };
}
