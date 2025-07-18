import { createResource } from "frappe-ui";

export const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  params: {
    doctype: "HD Ticket",
  },
  transform: (data) => {
    data = data
      .filter((field) => !field.fieldname.startsWith("_"))
      .map((field) => {
        return {
          label: field.label,
          value: field.fieldname,
          ...field,
        };
      });
    return data;
  },
});

export function formatTimeHMS(seconds) {
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  let formattedTime = "";

  if (days > 0) {
    formattedTime += `${days} days `;
  }

  if (hours > 0) {
    formattedTime += `${hours} hours `;
  }

  if (minutes > 0) {
    formattedTime += `${minutes} minutes `;
  }

  if (remainingSeconds > 0) {
    formattedTime += `${remainingSeconds} seconds`;
  }

  return formattedTime.trim();
}
