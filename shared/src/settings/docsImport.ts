import { frappeRequest } from "frappe-ui";
import { onBeforeUnmount, ref } from "vue";

export type ImportResult =
  | {
      state: "running";
      stage: "waiting" | "finding" | "reading";
      done: number;
      total: number;
      host: string;
    }
  | {
      state: "done";
      created: number;
      skipped: number;
      failed: number;
      host: string;
      category: string;
    }
  | { state: "error"; message: string; host: string };

const GIVE_UP = 5 * 60 * 1000;

export function viewDraftsHref(category: string) {
  return `/helpdesk/kb?category=${encodeURIComponent(category)}`;
}

// The last import, refreshed every `interval` ms while one is running.
export function useImportResult(interval: number) {
  const result = ref<ImportResult | null>(null);
  const timedOut = ref(false);
  let timer: ReturnType<typeof setTimeout> | undefined;
  let startedAt = 0;
  let active = false;

  function stop() {
    active = false;
    clearTimeout(timer);
    timer = undefined;
  }

  async function refresh() {
    clearTimeout(timer);
    try {
      // The endpoint only answers GET, and `call` always sends POST.
      result.value = await frappeRequest({
        url: "/api/method/helpdesk.api.docs_source.get_import_result",
        method: "GET",
      });
    } catch {
      // keep what is shown; the next tick tries again
    }
    if (!active || result.value?.state !== "running") return;
    if (Date.now() - startedAt > GIVE_UP) {
      timedOut.value = true;
      return;
    }
    timer = setTimeout(refresh, interval);
  }

  function watchRun() {
    active = true;
    startedAt = Date.now();
    timedOut.value = false;
    return refresh();
  }

  onBeforeUnmount(stop);
  return { result, timedOut, refresh: watchRun, stop };
}
