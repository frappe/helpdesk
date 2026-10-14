export const statusColorMap = {
  Completed: "green",
  Busy: "amber",
  Failed: "red",
  Initiated: "gray",
  Queued: "gray",
  Canceled: "gray",
  Ringing: "gray",
  "No Answer": "red",
  "In Progress": "blue",
};

export const statusLabelMap = {
  Completed: "Completed",
  Initiated: "Initiated",
  Busy: "Declined",
  Failed: "Failed",
  Queued: "Queued",
  Canceled: "Canceled",
  Ringing: "Ringing",
  "No Answer": "Missed Call",
  "In Progress": "In Progress",
};

// Spelt out so Tailwind's scanner sees every class. Keys are the values of
// statusColorMap, which stays bare because the list view feeds it to a Badge
// as a theme.
export const statusTextColorMap: Record<string, string> = {
  green: "text-green-600",
  amber: "text-amber-600",
  red: "text-red-600",
  gray: "text-gray-600",
  blue: "text-blue-600",
};
