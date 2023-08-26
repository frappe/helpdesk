export async function getPage(name: string) {
  const m = await import("@/pages");
  return m[name];
}
