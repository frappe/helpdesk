import { createResource } from "frappe-ui";
import type { App } from "vue";

function getTranslatedMessage(message: string): string {
    const translatedMessages = (("translatedMessages" in window ? window["translatedMessages"] : null) ?? {}) as Record<string, string>;
    return translatedMessages[message] || message;
}

function translateWithoutArgs(message: string): string {
    return getTranslatedMessage(message);
}

function translateWithArgs(message: string): { format: (...args: string[]) => string } {
    const translatedMessage = getTranslatedMessage(message);
    return {
        format(...args) {
            return translatedMessage.replace(/{(\d+)}/g, function (match, index) {
                return typeof args[index] != 'undefined' ? args[index] : match;
            })
        }
    }
};

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
    app.config.globalProperties.__ = translateWithoutArgs;
    app.config.globalProperties.__args = translateWithArgs;
    const windowObj = window as any;
    windowObj.__ = translateWithoutArgs;
    windowObj.__args = translateWithArgs;
    if (!windowObj.translatedMessages) {
        fetchTranslations();
    }
}

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    __: typeof translateWithoutArgs; 
    __args: typeof translateWithArgs;
  }
}
