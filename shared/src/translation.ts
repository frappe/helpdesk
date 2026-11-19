import { createResource } from "frappe-ui";
import { ref } from "vue";
import type { App } from "vue";

// Ref, so `__()` text re-renders on language change.
export const translations = ref<Record<string, string>>({});

type Replacement = string | number;

function translate(message: string): string;
function translate(message: string, ...args: Replacement[]): string;
function translate(message: string, args: Replacement[]): string;
function translate(
  message: string,
  ...args: (Replacement | Replacement[])[]
): string {
  const translatedMessage = translations.value[message] || message;
  const values = args.flat();
  if (values.length === 0) {
    return translatedMessage;
  }
  return translatedMessage.replace(/{(\d+)}/g, function (match, index) {
    const value = values[Number(index)];
    return value === undefined ? match : String(value);
  });
}

export const __ = translate;

let resource: ReturnType<typeof createResource> | null = null;

// Later calls refetch, e.g. after a language change.
export function fetchTranslations() {
  if (resource) return resource.reload();
  resource = createResource({
    url: "helpdesk.api.general.get_translations",
    method: "GET",
    cache: "translations",
    auto: true,
    transform(data: Record<string, string>) {
      translations.value = data || {};
      return data;
    },
  });
}

export function translationPlugin(app: App<Element>) {
  app.config.globalProperties.__ = translate;
  (window as any).__ = translate;
  fetchTranslations();
}
