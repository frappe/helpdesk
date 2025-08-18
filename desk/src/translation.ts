import { createResource } from "frappe-ui";
import type { App } from "vue";

function getTranslatedMessage(message: string): string {
    const translatedMessages = (("translatedMessages" in window ? window["translatedMessages"] : null) ?? {}) as Record<string, string>;
    return translatedMessages[message] || message;
}

function translate(message: string): string;
function translate(message: string, ...args: string[]): string;
function translate(message: string, ...args: string[]): string {
    const translatedMessage = getTranslatedMessage(message)
    if (args.length === 0) {
        return translatedMessage;
    }
    return translatedMessage.replace(/{(\d+)}/g, function (match, index) {
        return typeof args[index] != 'undefined' ? args[index] : match;
    });
}

export const __ = translate;

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
    __: typeof translate; 
  }
}
