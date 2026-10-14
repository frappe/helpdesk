/** Lets a local run target one bench site without an /etc/hosts entry. */
export function siteHeader(): Record<string, string> | undefined {
  const site = process.env.SITE_NAME;
  return site ? { "X-Frappe-Site-Name": site } : undefined;
}
