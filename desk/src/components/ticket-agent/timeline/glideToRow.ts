/**
 * Scrolls `scroller` so the row with id `rowId` sits mid-view, eased over
 * `durationMs`, and resolves once it lands. The browser's smooth scroll picks
 * its own duration and has no reliable "done", which the pinned bar waits on.
 */
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

function centerOffset(scroller: HTMLElement, row: Element): number {
  const view = scroller.getBoundingClientRect();
  const box = row.getBoundingClientRect();
  return box.top + box.height / 2 - (view.top + view.height / 2);
}

function easeOutCubic(progress: number): number {
  return 1 - (1 - progress) ** 3;
}
