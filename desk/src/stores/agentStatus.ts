import { useAuthStore } from "@/stores/auth";
import { userStorage } from "@/composables/userStorage";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { HDAgentStatus } from "@/types/doctypes";
import {
  createListResource,
  createResource,
  dayjs,
  dayjsLocal,
  toast,
  type Dayjs,
} from "frappe-ui";
import calendar from "dayjs/plugin/calendar";
import { defineStore } from "pinia";
import { computed, reactive, watch } from "vue";

dayjs.extend(calendar);

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

export interface ExpiryPreset {
  label: string;
  /** Chip form: "30m". */
  short: string;
  /** Null means the status never clears. */
  expiresOn: () => Dayjs | null;
  never?: true;
}

// the format frappe datetime fields are sent in
const DATETIME_FORMAT = "YYYY-MM-DD HH:mm:ss";
// 12-hour, e.g. "9:41 AM"
const TIME_FORMAT = "h:mm A";
// the longest delay setTimeout accepts
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

  function applyLive(
    agent: string,
    availability?: string,
    changedOn?: string,
    expiresOn?: string | null
  ) {
    if (!agent || !availability) return;
    liveStatuses[agent] = {
      availability,
      changedOn: changedOn ?? "",
      expiresOn: expiresOn ?? "",
    };
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
    onSuccess: () => toast.success(__("Status updated successfully.")),
    onError: () => toast.error(__("Could not update status.")),
  });

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

  function setMyStatus(status: string) {
    if (!status || status === myStatus.value) return;
    // changedOn is left empty — it is never rendered for our own dot and the
    // socket echo overwrites it with the authoritative server timestamp. The
    // server drops the timer on a new status, so drop it here too.
    saveMyAvailability(
      { availability: status },
      { availability: status, changedOn: "", expiresOn: "" }
    );
  }

  // back to the default status, as the timer would have done
  function clearMyStatus() {
    setMyStatus(auth.defaultAgentStatus);
  }

  function applyExpiryPreset(preset: ExpiryPreset) {
    // presets are on the agent's clock, the server stores system time
    const expiresOn =
      preset.expiresOn()?.tz(window.timezone?.system).format(DATETIME_FORMAT) ??
      null;
    if ((expiresOn || "") === myStatusExpiresOn.value) return;
    saveMyAvailability(
      { availability_expires_on: expiresOn },
      { expiresOn: expiresOn || "" }
    );
  }

  // the open tab clears the status on time; the scheduler covers closed tabs
  let expiryTimer: ReturnType<typeof setTimeout> | undefined;
  watch(
    myStatusExpiresOn,
    (expiresOn) => {
      clearTimeout(expiryTimer);
      if (!expiresOn) return;
      const delay = dayjsLocal(expiresOn).diff(dayjsLocal());
      // setTimeout fires at once past ~24.8 days; leave those to the scheduler
      if (delay > MAX_TIMEOUT) return;
      expiryTimer = setTimeout(clearMyStatus, Math.max(0, delay));
    },
    { immediate: true }
  );

  // only "Never" can show as picked: a stored time does not say which
  // preset made it
  function isExpiryPresetActive(preset: ExpiryPreset): boolean {
    return !myStatusExpiresOn.value && Boolean(preset.never);
  }

  function saveMyAvailability(
    values: Record<string, string | null>,
    livePatch: Partial<LiveAvailability>
  ) {
    if (!myAgentName) return;
    // Optimistic: update immediately, then roll back if the server rejects it.
    const previous = liveStatuses[myAgentName];
    liveStatuses[myAgentName] = {
      availability: "",
      changedOn: "",
      expiresOn: "",
      ...previous,
      ...livePatch,
    };
    setMyAvailability.submit(
      { doctype: "HD Agent", name: myAgentName, fieldname: values },
      {
        onError: () => {
          if (previous) liveStatuses[myAgentName] = previous;
          else delete liveStatuses[myAgentName];
        },
      }
    );
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

/** "Clear after" choices. A function so labels translate at render. */
export function expiryPresets(): ExpiryPreset[] {
  const after = (amount: number, unit: "minute" | "hour") => () =>
    dayjsLocal().add(amount, unit);
  return [
    { label: __("30 minutes"), short: "30m", expiresOn: after(30, "minute") },
    { label: __("1 hour"), short: "1h", expiresOn: after(1, "hour") },
    { label: __("4 hours"), short: "4h", expiresOn: after(4, "hour") },
    {
      label: __("Today"),
      short: __("Today"),
      expiresOn: () => dayjsLocal().endOf("day"),
    },
    {
      label: __("This week"),
      short: __("This week"),
      expiresOn: () => dayjsLocal().endOf("week"),
    },
    {
      label: __("Never"),
      short: __("Never"),
      never: true,
      expiresOn: () => null,
    },
  ];
}

/** Button text for a system-time expiry, on the agent's clock:
 * "9:41 AM", "Tomorrow 9:41 AM", "Thu 9:41 AM", "30 Oct". */
export function expiryLabel(expiresOn: string): string {
  if (!expiresOn) return "";
  const local = dayjsLocal(expiresOn);
  const date = dateFormat(local);
  return local.calendar(dayjsLocal(), {
    sameDay: TIME_FORMAT,
    nextDay: `[${__("Tomorrow")}] ${TIME_FORMAT}`,
    nextWeek: `ddd ${TIME_FORMAT}`,
    sameElse: date,
    lastDay: date,
    lastWeek: date,
  });
}

/** Sentence form: "Clears today at 9:41 AM", "Clears on 30 Oct at 9:41 AM". */
export function expirySummary(expiresOn: string): string {
  if (!expiresOn) return __("Clear status after");
  const local = dayjsLocal(expiresOn);
  const time = local.format(TIME_FORMAT);
  const onDate = () =>
    __("Clears on {0} at {1}", [local.format(dateFormat(local)), time]);
  return local.calendar(dayjsLocal(), {
    sameDay: () => __("Clears today at {0}", [time]),
    nextDay: () => __("Clears tomorrow at {0}", [time]),
    nextWeek: () => __("Clears {0} at {1}", [local.format("dddd"), time]),
    sameElse: onDate,
    lastDay: onDate,
    lastWeek: onDate,
  });
}

// the year only when it is not this one
function dateFormat(local: Dayjs): string {
  return local.isSame(dayjsLocal(), "year") ? "D MMM" : "D MMM YYYY";
}
