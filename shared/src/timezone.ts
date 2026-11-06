import { ref } from "vue";
import { dayjsLocal as frappeDayjsLocal, setConfig } from "frappe-ui";
import { dateFormat as frappeDateFormat } from "@framework/ui/components/ActivityTimeline/utils";


const zone = ref<string | null>(null);

export function setLocalTimezone(value: string | null) {
  setConfig("localTimezone", value);
  zone.value = value;
}

export function dayjsLocal(date?: string) {
  void zone.value;
  return frappeDayjsLocal(date);
}

export function dateFormat(date?: string, format?: string) {
  void zone.value;
  return frappeDateFormat(date, format);
}
