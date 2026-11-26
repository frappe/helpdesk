import type { KnowledgeBaseLink } from "./knowledgeBasePreview";

export type FooterColumn = { title: string; links: KnowledgeBaseLink[] };

export type KnowledgeBaseFooter = {
  tagline: string;
  copyright: string;
  columns: FooterColumn[];
  socials: KnowledgeBaseLink[];
};

type FooterRow = {
  label: string;
  url?: string;
  parent_label?: string;
  open_in_new_tab?: number | boolean;
};

export const MAX_FOOTER_COLUMNS = 4;

/** HD Settings stores footer_items as flat rows: a row without parent_label is a column,
 * a link row names its column in parent_label. This groups the links under their column. */
export function nestFooterRows(
  settings: Record<string, any>
): KnowledgeBaseFooter {
  const rows: FooterRow[] = settings.footer_items || [];
  return {
    tagline: settings.footer_tagline || "",
    copyright: settings.footer_copyright || "",
    columns: rows
      .filter((row) => !row.parent_label)
      .map((column) => ({
        title: column.label,
        links: rows
          .filter((row) => row.parent_label === column.label)
          .map(rowToLink),
      }))
      .filter((column) => column.links.length),
    socials: (settings.social_links || []).map(rowToLink),
  };
}

export function flattenFooterColumns(footer: KnowledgeBaseFooter) {
  return {
    footer_tagline: footer.tagline,
    footer_copyright: footer.copyright,
    footer_items: footer.columns.flatMap((column) => [
      { label: column.title },
      ...column.links.map((link) => ({
        ...linkToRow(link),
        parent_label: column.title,
      })),
    ]),
    social_links: footer.socials.map(linkToRow),
  };
}

function rowToLink({ label, url, open_in_new_tab }: FooterRow) {
  return { label, url: url || "", open_in_new_tab: Boolean(open_in_new_tab) };
}

function linkToRow(link: KnowledgeBaseLink) {
  return { ...link, open_in_new_tab: link.open_in_new_tab ? 1 : 0 };
}
