// TODO: drop after #3846/#3847 merge; import from shared directly.
import { __ } from "@helpdesk/shared/translation";

export { __, translationPlugin } from "@helpdesk/shared/translation";

declare module "@vue/runtime-core" {
  interface ComponentCustomProperties {
    __: typeof __;
  }
}
