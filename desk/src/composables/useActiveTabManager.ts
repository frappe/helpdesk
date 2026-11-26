import { useTelephonyStore } from "@/stores/telephony";
import { storeToRefs } from "pinia";
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

/**
 * Keeps the selected tab in sync with the URL hash. frappe-ui v1 Tabs are
 * keyed by `tab.value`, so this tracks the value rather than an index; the
 * first tab is the default and carries no hash.
 */
export function useActiveTabManager(tabs) {
  const route = useRoute();
  const router = useRouter();
  const telephonyStore = useTelephonyStore();
  const { isLoading: isTelephonyLoading } = storeToRefs(telephonyStore);

  const activeTab = ref("");

  const firstTab = () => tabs.value?.[0]?.value;

  const changeTabTo = (tab) => {
    activeTab.value = tab;
    if (tab === firstTab()) {
      router.replace({ path: route.path, query: route.query });
    } else {
      setActiveTabInUrl(tab);
    }
  };

  function setActiveTabInUrl(tab) {
    const hash = "#" + tab?.toLowerCase();
    if (route.hash === hash) return;
    router.push({ hash, query: route.query });
  }

  function findTab(hash) {
    return tabs.value?.find((tab) => tab.value.toLowerCase() === hash)?.value;
  }

  const setActiveTab = () => {
    const fromHash = findTab(route.hash.replace("#", ""));
    if (fromHash) {
      activeTab.value = fromHash;
      setActiveTabInUrl(fromHash);
      return;
    }

    activeTab.value = firstTab();
    router.replace({ path: route.path, query: route.query });
  };

  // Handle when page is navigated
  watch(
    () => route.hash,
    (newHash) => {
      const tab = findTab(newHash.replace("#", "")) ?? firstTab();

      if (tab === firstTab()) {
        router.replace({ path: route.path, query: route.query });
      }

      activeTab.value = tab;
    }
  );

  // Handle when tabs array is updated. `immediate` also applies the URL hash
  // when the panel remounts on soft navigation between tickets.
  watch(
    [tabs, isTelephonyLoading],
    ([tabsValue, isLoading]) => {
      if (!tabsValue?.length) return;
      if (!isLoading) {
        setActiveTab();
      }
    },
    { deep: true, flush: "post", immediate: true }
  );

  return { activeTab, changeTabTo };
}
