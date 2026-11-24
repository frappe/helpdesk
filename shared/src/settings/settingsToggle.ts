import { toast } from "frappe-ui";
import { __ } from "../translation";

/** Saves one switch; a click while a save is running is dropped, as a second save would fail on the stale timestamp. */
export function saveToggle(settings, fieldname: string, value: boolean) {
  if (settings.setValue.loading) return;
  settings.setValue.submit(
    { [fieldname]: value },
    { onSuccess: () => toast.success(__("Settings updated")) }
  );
}
