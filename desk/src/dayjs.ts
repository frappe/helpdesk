import d from "dayjs";
import localizedFormat from "dayjs/plugin/localizedFormat";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();
declare module "dayjs" {
  interface Dayjs {
    /** Example: `Aug 15, 2:29 AM` */
    short(): string;
    /** Example: `Tuesday, August 15, 2023 2:29 AM` */
    long(): string;
  }
}

d.extend(localizedFormat);
d.extend(relativeTime);
d.extend(function (_, cls) {
  cls.prototype.short = function () {
    return this.format("MMM D, h:mm A");
  };
  cls.prototype.long = function () {
    return this.format("LLLL");
  };
});
d.extend(utc);
d.extend(timezone);
d.tz.setDefault(authStore.timezone);

export const dayjs = d;
