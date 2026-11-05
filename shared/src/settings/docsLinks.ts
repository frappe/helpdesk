import { __ } from "../translation";

// The desk is a separate app, so it needs a full href.
export const articleHref = (name: string) => `/helpdesk/kb/articles/${name}`;

export const pagesLabel = (n: number) =>
  n === 1 ? __("Convert 1 page") : n ? __("Convert {0} pages", [n]) : __("Convert");
