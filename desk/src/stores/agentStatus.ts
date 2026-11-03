import { useAuthStore } from "@/stores/auth";
import { userStorage } from "@/composables/userStorage";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { HDAgentStatus } from "@/types/doctypes";
import { type ExpiryPreset } from "@/stores/statusExpiry";
import { serverInstant } from "@helpdesk/shared/utils";
import { useEventListener } from "@vueuse/core";
import { createListResource, createResource, toast } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, reactive, ref, watch } from "vue";

interface LiveAvailability {
  availability: string;
  changedOn: string;
  /** When the status clears, in system time. Empty when it never does. */
  expiresOn: string;
}

interface AvailabilityEvent {
  agent: string;
  availability: string;
  availability_changed_on: string;
  availability_expires_on: string | null;
  changed_by: string;
}

type SavedAvailability = Pick<
  AvailabilityEvent,
  "availability" | "availability_changed_on" | "availability_expires_on"
>;

const MAX_TIMEOUT = 2 ** 31 - 1;

// Maps an HD Agent Status `color` value to a solid presence-dot background.
const dotColorMap: Record<string, string> = {
  black: "bg-surface-gray-9",
  gray: "bg-surface-gray-6",
  blue: "bg-surface-blue-6",
  green: "bg-surface-green-6",
  red: "bg-surface-red-6",
  pink: "bg-surface-pink-6",
  orange: "bg-surface-orange-6",
  amber: "bg-surface-amber-6",
  yellow: "bg-surface-yellow-6",
  cyan: "bg-surface-cyan-6",
  teal: "bg-surface-teal-6",
  violet: "bg-surface-violet-6",
  purple: "bg-surface-purple-6",
};

const defaultColor = "bg-surface-gray-8";

export const useAgentStatusStore = defineStore("agentStatus", () => {
  // Set only for sessions that have an HD Agent record; null otherwise.
  const myAgentName = window.agent;

  // One status change = one greeting per device. An empty marker means this
  // device has no baseline yet: record without greeting, so a fresh browser
  // is not told about changes that predate it.
  const lastSeenStatusChange = userStorage("hd_status_change_seen", "");

  function noteStatusChange(
    availability: string,
    changedOn: string,
    changedBy: string
  ) {
    if (!changedOn || changedOn === lastSeenStatusChange.value) return;
    const firstVisit = !lastSeenStatusChange.value;
    lastSeenStatusChange.value = changedOn;
    if (firstVisit || !changedBy || changedBy === window.session_user) return;
    // status names are translated in the picker, so translate here too
    toast.info(__("Your status was changed to {0}.", __(availability)));
  }

  const statuses = createListResource({
    doctype: "HD Agent Status",
    cache: ["HD Agent Status", "list"],
    fields: [
      "name",
      "agent_status",
      "category",
      "color",
      "enabled",
      "status_order",
    ],
    orderBy: "`tabHD Agent Status`.status_order",
    pageLength: 1000,
    auto: true,
  });

  // Live availability keyed by HD Agent name. Seeded by fetches and kept current
  // over the socket — HD Agent's on_update broadcasts to every client, so this is
  // the single source of truth for "who is what right now", including ourselves.
  const liveStatuses = reactive<Record<string, LiveAvailability>>({});

  let confirmed: LiveAvailability | undefined;
  let pendingSaves = 0;

  function applyLive(
    agent: string,
    availability?: string,
    changedOn?: string,
    expiresOn?: string | null
  ) {
    if (!agent || !availability) return;
    const state = {
      availability,
      changedOn: changedOn ?? "",
      expiresOn: expiresOn ?? "",
    };
    if (agent === myAgentName) {
      confirmed = state;
      // an earlier save's echo would undo the patches still queued
      if (pendingSaves) return;
    }
    liveStatuses[agent] = state;
  }

  function restoreConfirmed() {
    if (!myAgentName) return;
    if (confirmed) liveStatuses[myAgentName] = confirmed;
    else delete liveStatuses[myAgentName];
  }

  const { $socket } = globalStore();
  $socket.on("agent_availability_updated", (data: AvailabilityEvent) => {
    if (data.agent === myAgentName) {
      noteStatusChange(
        data.availability,
        data.availability_changed_on,
        data.changed_by
      );
    }
    applyLive(
      data.agent,
      data.availability,
      data.availability_changed_on,
      data.availability_expires_on
    );
  });

  // Seed our own status from the session payload (auth.get_user already resolves
  // the agent), then let the socket and the optimistic write keep it current — no
  // dedicated fetch and no reload.
  const auth = useAuthStore();
  watch(
    () => auth.availability,
    (availability) =>
      applyLive(
        myAgentName ?? "",
        availability,
        auth.availabilityChangedOn,
        auth.availabilityExpiresOn
      ),
    { immediate: true }
  );

  // greet a login that missed the live toast
  if (myAgentName) {
    noteStatusChange(
      auth.availability,
      auth.availabilityChangedOn,
      auth.availabilityChangedBy
    );
  }

  // A plain document write: HD Agent's controller owns the validation, the
  // availability_changed_on stamp and the socket broadcast, so every write path
  // behaves the same and this needs no dedicated endpoint.
  const setMyAvailability = createResource({
    url: "frappe.client.set_value",
  });

  let pendingSave = Promise.resolve();

  const myStatus = computed(
    () => (myAgentName && liveStatuses[myAgentName]?.availability) || ""
  );

  const myStatusExpiresOn = computed(
    () => (myAgentName && liveStatuses[myAgentName]?.expiresOn) || ""
  );

  function statusCanExpire(status: string): boolean {
    const category = getStatus(status)?.category;
    return Boolean(category) && category !== "Active";
  }

  // Selectable statuses, derived from the same list the presence dots use so the
  // menu and the dots never disagree and we avoid a second server round-trip.
  const statusOptions = computed<string[]>(() =>
    (statuses.data ?? [])
      .filter((s: HDAgentStatus) => s.enabled)
      .map((s: HDAgentStatus) => s.agent_status)
  );

  function setMyStatus(status: string, { quiet = false } = {}) {
    if (!status || status === myStatus.value) return;
    // changedOn is left empty — it is never rendered for our own dot and the
    // socket echo overwrites it with the authoritative server timestamp. The
    // server drops the timer on a new status, so drop it here too.
    saveMyAvailability(
      { availability: status },
      { availability: status, changedOn: "", expiresOn: "" },
      { quiet }
    );
  }

  function clearMyStatus() {
    setMyStatus(auth.defaultAgentStatus);
  }

  // a stored time does not say which preset made it
  const pickedPreset = ref<{ label: string; expiresOn: string }>();

  function applyExpiryPreset(preset: ExpiryPreset) {
    // presets are on the agent's clock, the server stores system time
    const expiresOn =
      preset
        .expiresOn()
        ?.tz(window.timezone?.system)
        .format("YYYY-MM-DD HH:mm:ss") ?? null;
    if ((expiresOn || "") === myStatusExpiresOn.value) return;
    pickedPreset.value = { label: preset.label, expiresOn: expiresOn || "" };
    saveMyAvailability(
      { availability_expires_on: expiresOn },
      { expiresOn: expiresOn || "" }
    );
  }

  let expiryTimer: ReturnType<typeof setTimeout> | undefined;
  watch(
    myStatusExpiresOn,
    (expiresOn) => {
      clearTimeout(expiryTimer);
      if (expiresOn) armExpiryTimer(expiresOn);
    },
    { immediate: true }
  );

  function armExpiryTimer(expiresOn: string) {
    const delay = serverInstant(expiresOn).diff();
    // setTimeout fires at once past ~24.8 days: wake at the cap, measure again
    expiryTimer = setTimeout(
      () =>
        delay > MAX_TIMEOUT
          ? armExpiryTimer(expiresOn)
          : clearExpiredStatus(expiresOn),
      Math.min(Math.max(0, delay), MAX_TIMEOUT)
    );
  }

  // quiet: a failure is usually another tab clearing it first
  function clearExpiredStatus(expiresOn: string) {
    if (myStatusExpiresOn.value !== expiresOn) return;
    setMyStatus(auth.defaultAgentStatus, { quiet: true });
  }

  // a sleeping laptop holds the timer back; catch up when the tab is seen again
  useEventListener(document, "visibilitychange", () => {
    const expiresOn = myStatusExpiresOn.value;
    if (document.visibilityState !== "visible" || !expiresOn) return;
    if (serverInstant(expiresOn).diff() <= 0) clearExpiredStatus(expiresOn);
  });

  function isExpiryPresetActive(preset: ExpiryPreset): boolean {
    const expiresOn = myStatusExpiresOn.value;
    if (preset.never) return !expiresOn;
    const picked = pickedPreset.value;
    // the server echo can format the time differently, so compare instants
    return (
      Boolean(expiresOn && picked?.expiresOn) &&
      picked?.label === preset.label &&
      serverInstant(picked.expiresOn).isSame(serverInstant(expiresOn))
    );
  }

  function saveMyAvailability(
    values: Record<string, string | null>,
    livePatch: Partial<LiveAvailability>,
    { quiet = false } = {}
  ) {
    if (!myAgentName) return;
    liveStatuses[myAgentName] = {
      availability: "",
      changedOn: "",
      expiresOn: "",
      ...liveStatuses[myAgentName],
      ...livePatch,
    };
    pendingSaves++;
    const confirmedWhenQueued = confirmed;
    // Queue saves: set_value checks the modified stamp, so parallel writes fail.
    pendingSave = pendingSave.then(() =>
      submitMyAvailability(values, quiet, confirmedWhenQueued)
    );
  }

  async function submitMyAvailability(
    values: Record<string, string | null>,
    quiet: boolean,
    confirmedWhenQueued: LiveAvailability | undefined
  ) {
    try {
      const agent: SavedAvailability = await setMyAvailability.submit({
        doctype: "HD Agent",
        name: myAgentName,
        fieldname: values,
      });
      markMyAvailabilitySaved(agent, quiet);
    } catch {
      revertMyAvailability(quiet, confirmedWhenQueued);
    }
  }

  function markMyAvailabilitySaved(agent: SavedAvailability, quiet: boolean) {
    pendingSaves--;
    if (!quiet) toast.success(__("Status updated successfully."));
    applyLive(
      myAgentName,
      agent.availability,
      agent.availability_changed_on,
      agent.availability_expires_on
    );
  }

  function revertMyAvailability(
    quiet: boolean,
    confirmedWhenQueued: LiveAvailability | undefined
  ) {
    pendingSaves--;
    if (!quiet) toast.error(__("Could not update status."));
    // a queued save settles the state when it lands
    if (pendingSaves) return;
    // restoring an expired status would re-arm its timer
    if (quiet && confirmed === confirmedWhenQueued) return;
    restoreConfirmed();
  }

  function getStatus(name: string): HDAgentStatus | undefined {
    return statuses.data?.find((s: HDAgentStatus) => s.agent_status === name);
  }

  function statusColor(name: string): string {
    const color = getStatus(name)?.color?.toLowerCase();
    return (color && dotColorMap[color]) || defaultColor;
  }

  return {
    statuses,
    liveStatuses,
    myStatus,
    myStatusExpiresOn,
    statusCanExpire,
    statusOptions,
    setMyStatus,
    clearMyStatus,
    applyExpiryPreset,
    isExpiryPresetActive,
    getStatus,
    statusColor,
  };
});
