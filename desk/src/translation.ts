import { createResource } from "frappe-ui";
import type { App } from "vue";
import { ref } from "vue";

// Reactive signal for when translations are loaded
export const translationsLoaded = ref(false);

function getTranslatedMessage(message: string): string {
    const translatedMessages = (("translatedMessages" in window ? window["translatedMessages"] : null) ?? {}) as Record<string, string>;
    return translatedMessages[message] || message;
}

function translate(message: string): string;
function translate(message: string, ...args: string[]): string;
function translate(message: string, ...args: string[]): string {
    // Access the ref to create dependency for computed properties
    if (translationsLoaded.value) {
        // This ensures computed properties re-evaluate when translations load
    }
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
            translationsLoaded.value = true;
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
