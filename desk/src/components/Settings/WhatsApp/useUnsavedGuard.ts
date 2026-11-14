import { onUnmounted, ref, watch } from "vue";
import { disableSettingModalOutsideClick } from "../settingsModal";

/**
 * Keeps the settings modal open and tabs guarded while `isDirty` is true,
 * and asks before `leave` runs an action that would drop the edits.
 */
export function useUnsavedGuard(isDirty: () => boolean) {
  const confirming = ref(false);
  let pending: (() => void) | null = null;

  function leave(action: () => void) {
    if (!isDirty()) return action();
    pending = action;
    confirming.value = true;
  }

  function confirm() {
    confirming.value = false;
    disableSettingModalOutsideClick.value = false;
    pending?.();
    pending = null;
  }

  watch(isDirty, (dirty) => (disableSettingModalOutsideClick.value = dirty), {
    immediate: true,
  });
  onUnmounted(() => (disableSettingModalOutsideClick.value = false));

  return { confirming, leave, confirm };
}
