import { useEventListener, useStorage } from "@vueuse/core";
import type { WindowMode } from "frappe-ui/experimental";
import { computed, ref, type Ref } from "vue";

const MIN_BODY_HEIGHT = 240;
// Dragging this far below the minimum collapses the window back to the pill.
const MINIMIZE_OVERDRAG = 60;

// Dragging the docked title bar sets the body column's height; 0 means
// natural. The window's own resize only exists while floating.
export function useDockedResize(options: {
  windowMode: Readonly<Ref<WindowMode>>;
  column: Ref<HTMLElement | null>;
  isMobileView: Readonly<Ref<boolean>>;
  onCollapse: () => void;
}) {
  const { windowMode, column, isMobileView, onCollapse } = options;
  const dockedHeight = useStorage("helpdesk-composer-height", 0);

  const dockedColumnStyle = computed(() =>
    windowMode.value === "docked" && dockedHeight.value > 0
      ? { height: `${dockedHeight.value}px` }
      : undefined
  );

  function clampBodyHeight(value: number) {
    return Math.min(
      Math.max(value, MIN_BODY_HEIGHT),
      Math.round(window.innerHeight * 0.8)
    );
  }

  // The live drag; move/up listeners are registered once below and no-op while
  // this is null, so nothing can stack or leak.
  let resizing: { startY: number; startHeight: number } | null = null;
  // A pointer released outside the window must not count as an outside click.
  const justResized = ref(false);

  function onPanelPointerDown(event: PointerEvent) {
    if (windowMode.value !== "docked" || isMobileView.value) return;
    const target = event.target as HTMLElement;
    if (target.closest("button, a, input, select, textarea, [role='button']"))
      return;
    if (column.value?.contains(target)) return;
    event.preventDefault();
    startDockedResize(event);
  }

  function startDockedResize(event: PointerEvent) {
    resizing = { startY: event.clientY, startHeight: currentBodyHeight() };
    try {
      (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
    } catch {}
  }

  function currentBodyHeight() {
    return dockedHeight.value || column.value?.offsetHeight || MIN_BODY_HEIGHT;
  }

  function resizeDockedBy(delta: number) {
    dockedHeight.value = clampBodyHeight(currentBodyHeight() + delta);
  }

  useEventListener(window, "pointermove", (event: PointerEvent) => {
    if (!resizing) return;
    const next = resizing.startHeight + (resizing.startY - event.clientY);
    if (next < MIN_BODY_HEIGHT - MINIMIZE_OVERDRAG) {
      // Dragged well past the floor: collapse to the pill, keeping the pre-drag
      // height so reopening restores it.
      const previous = resizing.startHeight;
      stopDockedResize();
      dockedHeight.value = clampBodyHeight(previous);
      onCollapse();
      return;
    }
    dockedHeight.value = clampBodyHeight(next);
  });
  useEventListener(window, "pointerup", stopDockedResize);
  useEventListener(window, "pointercancel", stopDockedResize);

  function stopDockedResize() {
    if (!resizing) return;
    resizing = null;
    justResized.value = true;
    // The click event fires after pointerup; lift the guard a task later.
    setTimeout(() => (justResized.value = false), 0);
  }

  return {
    dockedHeight,
    dockedColumnStyle,
    justResized,
    onPanelPointerDown,
    startDockedResize,
    resizeDockedBy,
  };
}
