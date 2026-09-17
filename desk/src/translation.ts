import { __ } from "@helpdesk/shared/translation";

export { __, translationPlugin } from "@helpdesk/shared/translation";

// `translationPlugin` puts `__` on every component instance; type it for templates.
declare module "@vue/runtime-core" {
  interface ComponentCustomProperties {
    __: typeof __;
  }
}
