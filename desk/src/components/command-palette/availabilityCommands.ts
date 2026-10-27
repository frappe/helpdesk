import {
  expiryLabel,
  expiryPresets,
  useAgentStatusStore,
} from "@/stores/agentStatus";
import { parseColor } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { GROUP, type Command } from "./paletteTypes";

import LucideActivity from "~icons/lucide/activity";
import LucideClock from "~icons/lucide/clock";

/** Account rows for the agent's own status, plus its timer when it can expire. */
export function availabilityCommands(): Command[] {
  const store = useAgentStatusStore();
  return [
    {
      id: "availability",
      title: __("Set availability"),
      group: GROUP.account,
      icon: LucideActivity,
      // Live status names too, so site-defined values ("Lunch") match.
      keywords:
        "my status presence online offline away busy " +
        store.statusOptions.join(" "),
      children: () => availabilityChildren(),
    },
    ...(store.statusCanExpire(store.myStatus) ? [statusExpiryCommand()] : []),
  ];
}

async function availabilityChildren(): Promise<Command[]> {
  const store = useAgentStatusStore();
  // The level snapshots this result; a cold store would freeze it empty.
  await store.statuses.list.promise;
  return (store.statusOptions ?? []).map((status: string) => ({
    id: `availability-${status}`,
    title: __(status),
    group: "Set availability",
    dotClass: parseColor(store.getStatus(status)?.color ?? "Gray"),
    checked: status === store.myStatus,
    // an away status drills straight into its timer, as the popover does
    ...(store.statusCanExpire(status)
      ? {
          children: () => {
            store.setMyStatus(status);
            return expiryChildren();
          },
        }
      : { perform: () => store.setMyStatus(status) }),
  }));
}

function statusExpiryCommand(): Command {
  const store = useAgentStatusStore();
  const expiresAt = expiryLabel(store.myStatusExpiresOn);
  return {
    id: "availability-expiry",
    title: __("Clear status after"),
    ...(expiresAt && { titleSuffix: expiresAt }),
    group: GROUP.account,
    icon: LucideClock,
    keywords: "status timer expire reset until snooze away",
    children: () => expiryChildren(),
  };
}

function expiryChildren(): Command[] {
  const store = useAgentStatusStore();
  return [
    ...expiryPresets().map((preset) => ({
      id: `availability-expiry-${preset.label}`,
      title: preset.label,
      group: __("Clear status after"),
      checked: store.isExpiryPresetActive(preset),
      perform: () => store.applyExpiryPreset(preset),
    })),
    {
      id: "availability-expiry-clear-now",
      title: __("Clear now"),
      group: __("Clear status after"),
      perform: () => store.clearMyStatus(),
    },
  ];
}
