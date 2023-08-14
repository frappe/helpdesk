import d from "dayjs";
import localizedFormat from "dayjs/plugin/localizedFormat";
import relativeTime from "dayjs/plugin/relativeTime";
import timezone from "dayjs/plugin/timezone";
import updateLocale from "dayjs/plugin/updateLocale";
import utc from "dayjs/plugin/utc";

d.extend(localizedFormat);
d.extend(relativeTime);
d.extend(timezone);
d.extend(updateLocale);
d.extend(utc);

export const dayjs = d;
