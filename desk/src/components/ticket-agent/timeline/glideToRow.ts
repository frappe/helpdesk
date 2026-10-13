/** Eases the row to mid-view and resolves on arrival; the browser's smooth
 * scroll has no reliable "done", and the pinned bar waits on it. */
export function glideToRow(
  scroller: HTMLElement,
  rowId: string,
  durationMs: number
): Promise<void> {
  const row = scroller.querySelector(`[id="${CSS.escape(rowId)}"]`);
  if (!row) return Promise.resolve();
  const from = scroller.scrollTop;
  const to = from + centerOffset(scroller, row);
  if (to === from || matchMedia("(prefers-reduced-motion: reduce)").matches) {
    scroller.scrollTop = to;
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    const start = performance.now();
    const step = (now: number) => {
      const progress = Math.min((now - start) / durationMs, 1);
      scroller.scrollTop = from + (to - from) * easeOutCubic(progress);
      if (progress < 1) requestAnimationFrame(step);
      else resolve();
    };
    requestAnimationFrame(step);
  });
}

// centre below the scroll padding like scrollIntoView, or the flash's own
// scroll after the glide nudges the row by half the padding
function centerOffset(scroller: HTMLElement, row: Element): number {
  const view = scroller.getBoundingClientRect();
  const box = row.getBoundingClientRect();
  const padding = parseFloat(getComputedStyle(scroller).scrollPaddingTop) || 0;
  const viewCenter = view.top + padding + (view.height - padding) / 2;
  return box.top + box.height / 2 - viewCenter;
}

function easeOutCubic(progress: number): number {
  return 1 - (1 - progress) ** 3;
}
