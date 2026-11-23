import type { KnowledgeBaseLink } from "./knowledgeBasePreview";

export type FooterColumn = { title: string; links: KnowledgeBaseLink[] };

export type KnowledgeBaseFooter = {
  enabled: boolean;
  tagline: string;
  copyright: string;
  columns: FooterColumn[];
  socials: KnowledgeBaseLink[];
};

type FooterItem = {
  label: string;
  url?: string;
  parent_label?: string;
  open_in_new_tab?: number | boolean;
};

export const MAX_FOOTER_COLUMNS = 4;

/** Reads the footer from HD Settings fields; footer_items nest like Website Settings' footer. */
export function footerFromSettings(
  settings: Record<string, any>
): KnowledgeBaseFooter {
  const items: FooterItem[] = settings.footer_items || [];
  return {
    enabled: Boolean(settings.show_footer),
    tagline: settings.footer_tagline || "",
    copyright: settings.footer_copyright || "",
    columns: items
      .filter((item) => !item.parent_label)
      .map((column) => ({
        title: column.label,
        links: items
          .filter((item) => item.parent_label === column.label)
          .map(toLink),
      }))
      .filter((column) => column.links.length),
    socials: (settings.social_links || []).map(toLink),
  };
}

export function footerToSettings(footer: KnowledgeBaseFooter) {
  return {
    show_footer: footer.enabled ? 1 : 0,
    footer_tagline: footer.tagline,
    footer_copyright: footer.copyright,
    footer_items: footer.columns.flatMap((column) => [
      { label: column.title },
      ...column.links.map((link) => ({
        ...toRow(link),
        parent_label: column.title,
      })),
    ]),
    social_links: footer.socials.map(toRow),
  };
}

function toLink({ label, url, open_in_new_tab }: FooterItem) {
  return { label, url: url || "", open_in_new_tab: Boolean(open_in_new_tab) };
}

function toRow(link: KnowledgeBaseLink) {
  return { ...link, open_in_new_tab: link.open_in_new_tab ? 1 : 0 };
}
