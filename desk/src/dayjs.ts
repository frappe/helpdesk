import d from "dayjs";
import localizedFormat from "dayjs/plugin/localizedFormat";
import relativeTime from "dayjs/plugin/relativeTime";

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

export const dayjs = d;
