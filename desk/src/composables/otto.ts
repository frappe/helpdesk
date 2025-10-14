import { createResource } from "frappe-ui";

export const enabledAiFeatures = createResource({
  url: "helpdesk.api.otto.get_enabled_features",
  auto: true,
});

