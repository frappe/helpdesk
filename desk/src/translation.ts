import { createResource } from "frappe-ui";
import type { App } from "vue";

type Translate= (message: string) => string | {format: (...args: string[]) => string};

const translate: Translate = function (message) {
    const translatedMessages = (("translatedMessages" in window ? window["translatedMessages"] : null) ?? {}) as Record<string, string>;
    const translatedMessage = translatedMessages[message] || message;
    const hasPlaceholders = /{\d+}/.test(message);
    if (!hasPlaceholders) {
        return translatedMessage;
    }
    return {
        format(...args) {
            return translatedMessage.replace(/{(\d+)}/g, function (match, index) {
                return typeof args[index] != 'undefined' ? args[index] : match;
            })
        }
    }
}

function fetchTranslations() {
    createResource({
        url: "helpdesk.api.general.get_translations",
        method: "GET",
        cache: "translations",
        auto: true,
        transform(data: Record<string, string>) {
            (window as any).translatedMessages = data;
        }
    });
}

export function translationPlugin(app: App<Element>) {
    app.config.globalProperties.__ = translate;
    const windowObj = window as any;
    windowObj.__ = translate;
    if (!windowObj.translatedMessages) {
        fetchTranslations();
    }
}

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    __: Translate; 
  }
}
