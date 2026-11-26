import { createResource } from "frappe-ui";

export const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  params: {
    doctype: "HD Ticket",
    ignore_team_restrictions: true,
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
