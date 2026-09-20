import { useEventListener, useStorage, useWindowSize } from "@vueuse/core";
import type { WindowMode } from "frappe-ui/experimental";
import { computed, ref, type Ref } from "vue";

//mininum size of the composer upto which no collapse into docked state
const MIN_BODY_HEIGHT = 80;
const COLLAPSE_HEIGHT = 0;
// max height from top upto which it panel can be dragged
const THREAD_PEEK = 64;

// dragging the docked title bar sets the message area height, 0 means natural
export function useDockedResize(options: {
  windowMode: Readonly<Ref<WindowMode>>;
  column: Ref<HTMLElement | null>;
  root: Ref<HTMLElement | null>;
  onCollapse: () => void;
  onReopen: () => void;
}) {
  const { windowMode, column, root, onCollapse, onReopen } = options;
  const dockedHeight = useStorage("helpdesk-composer-height", 0);
  const { height: viewportHeight } = useWindowSize();

  // on toggle of cc and bcc increase the body height upwards
  const dockedBodyStyle = computed(() =>
    windowMode.value === "docked" && dockedHeight.value > 0
      ? { "--composer-body-height": `${clampBodyHeight(dockedHeight.value)}px` }
      : undefined
  );

  function clampBodyHeight(value: number) {
    const floor = resizing.value ? COLLAPSE_HEIGHT : MIN_BODY_HEIGHT;
    return Math.min(
      Math.max(value, floor),
      Math.round(viewportHeight.value * 0.7)
    );
  }

  // the live drag, null when there is none so the listeners below just no-op
  const resizing = ref<{
    startY: number;
    startHeight: number;
    minY: number;
    collapsed: boolean;
  } | null>(null);
  const isResizing = computed(() => resizing.value !== null);
  // A pointer released outside the window must not count as an outside click.
  const justResized = ref(false);

  function startDockedResize(event: PointerEvent) {
    const grabbed = event.currentTarget as HTMLElement;
    resizing.value = {
      startY: event.clientY,
      startHeight: currentBodyHeight(),
      //max height upto which panel can be dragged
      minY: threadTop() + (event.clientY - grabbed.getBoundingClientRect().top),
      collapsed: false,
    };

    try {
      (root.value ?? grabbed).setPointerCapture(event.pointerId);
    } catch {}
  }

  function threadTop() {
    const thread = document.querySelector(
      "[role='tabpanel'][data-state='active']"
    );
    return thread ? thread.getBoundingClientRect().top + THREAD_PEEK : 0;
  }

  function currentBodyHeight() {
    if (dockedHeight.value) return dockedHeight.value;
    //get exisiting height from the composer and set the other composer to same height
    const bodies =
      column.value?.querySelectorAll<HTMLElement>(".composer-body");
    const heights = Array.from(bodies ?? [], (body) => body.offsetHeight);
    return heights.length ? Math.min(...heights) : 0;
  }

  function resizeDockedBy(delta: number) {
    dockedHeight.value = clampBodyHeight(currentBodyHeight() + delta);
  }

  useEventListener(window, "pointermove", (event: PointerEvent) => {
    if (!resizing.value) return;
    const { startY, startHeight, minY, collapsed } = resizing.value;
    const next = startHeight + (startY - Math.max(event.clientY, minY));
    if (next <= COLLAPSE_HEIGHT) {
      if (!collapsed) {
        resizing.value.collapsed = true;
        dockedHeight.value = clampBodyHeight(startHeight);
        onCollapse();
      }
      return;
    }
    if (collapsed) {
      resizing.value.collapsed = false;
      onReopen();
    }
    dockedHeight.value = clampBodyHeight(next);
  });
  useEventListener(window, "pointerup", stopDockedResize);
  useEventListener(window, "pointercancel", stopDockedResize);

  function stopDockedResize() {
    if (!resizing.value) return;
    const { startHeight, collapsed } = resizing.value;
    const squeezed = !collapsed && dockedHeight.value < MIN_BODY_HEIGHT;
    resizing.value = null;
    if (squeezed) {
      dockedHeight.value = clampBodyHeight(startHeight);
      onCollapse();
    }
    justResized.value = true;
    // The click event fires after pointerup; lift the guard a task later.
    setTimeout(() => (justResized.value = false), 0);
  }

  return {
    dockedHeight,
    dockedBodyStyle,
    isResizing,
    justResized,
    startDockedResize,
    resizeDockedBy,
  };
}
