// TODO: after #3846/#3847 merge, import `@helpdesk/shared/translation` directly in the
// desk files that use `@/translation`, move the type below into a desk `.d.ts`, and delete this file.
import { __ } from "@helpdesk/shared/translation";

export { __, translationPlugin } from "@helpdesk/shared/translation";

// `translationPlugin` puts `__` on every component instance; type it for templates.
declare module "@vue/runtime-core" {
  interface ComponentCustomProperties {
    __: typeof __;
  }
}
