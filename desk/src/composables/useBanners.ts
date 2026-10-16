import { globalStore } from "@/stores/globalStore";
import { createResource } from "frappe-ui";

export type BannerName = "customer_portal_permission" | "ticket_field_permission";

const banners = createResource({
  url: "helpdesk.api.banners.get_banners",
  initialData: [],
});
const dismissResource = createResource({
  url: "helpdesk.api.banners.dismiss_banner",
});
let started = false;

export function useBanners() {
  if (!started) {
    started = true;
    banners.fetch();
    globalStore().$socket.on("helpdesk:settings-updated", () =>
      banners.reload()
    );
  }

  function isVisible(banner: BannerName): boolean {
    return banners.data.includes(banner);
  }

  async function dismiss(banner: BannerName): Promise<void> {
    await dismissResource.submit({ banner });
    banners.reload();
  }

  return { isVisible, dismiss };
}
