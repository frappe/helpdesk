import { createResource } from "frappe-ui";
import { computed, h } from "vue";

interface App {
  name: string;
  logo: string;
  title: string;
  route: string;
}

/**
 * Loads the list of Frappe apps the user can switch to and exposes them as
 * Dropdown submenu options (each with the app's logo as the row prefix).
 */
export function useApps() {
  const apps = createResource({
    url: "frappe.apps.get_apps",
    cache: "apps",
    auto: true,
    transform: (data: App[]) => {
      const _apps: App[] = [
        {
          name: "frappe",
          logo: "/assets/helpdesk/desk/desk.png",
          title: "Desk",
          route: "/desk/helpdesk",
        },
      ];
      data.forEach((app) => {
        if (app.name === "helpdesk") return;
        _apps.push({
          name: app.name,
          logo: app.logo,
          title: app.title,
          route: app.route,
        });
      });
      return _apps;
    },
  });

  const appsSubmenu = computed(() =>
    (apps.data || []).map((app: App) => ({
      label: app.title,
      slots: {
        prefix: () =>
          h("img", { src: app.logo, class: "size-5 shrink-0 rounded" }),
      },
      onClick: () => {
        window.location.href = app.route;
      },
    }))
  );

  return { apps, appsSubmenu };
}
