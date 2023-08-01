import { RouteLocationNamedRaw, useRoute, useRouter } from "vue-router";

export function useOrder() {
  const route = useRoute();
  const router = useRouter();

  function get() {
    const q = (route.query.sort as string) ?? "";
    const d = decodeURIComponent(q);
    return d;
  }

  function set(sort: string, r?: RouteLocationNamedRaw) {
    r = r || route;
    const q = encodeURIComponent(sort);
    router.push({ ...r, query: { ...r.query, sort: q } });
  }

  return {
    get,
    set,
  };
}
