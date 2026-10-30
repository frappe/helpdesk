import { globalStore } from "@/stores/globalStore";
import type { BillingTrial } from "@frappe/cloud-sdk";
import { createResource } from "frappe-ui";

export type BannerName =
  | "customer_portal_permission"
  | "ticket_field_permission"
  | "trial";
export type Banner = { name: BannerName; trial?: BillingTrial };

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

  function banner(name: BannerName): Banner | undefined {
    return banners.data.find((b: Banner) => b.name === name);
  }

  function isVisible(name: BannerName): boolean {
    return !!banner(name);
  }

  async function dismiss(name: BannerName): Promise<void> {
    await dismissResource.submit({ banner: name });
    banners.reload();
  }

  return { banner, isVisible, dismiss, reload: () => banners.reload() };
}
