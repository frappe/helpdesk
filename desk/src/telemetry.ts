import { useTelemetry } from "frappe-ui/frappe";
import "../../../frappe/frappe/public/js/lib/posthog.js";
const APP = "helpdesk";

interface CaptureOptions {
  data: {
    [key: string]: string | number | boolean | object;
  };
}

export function capture(event: string, options: CaptureOptions = { data: {} }) {
  const { capture: _capture } = useTelemetry();
  _capture(event, options.data);
}
