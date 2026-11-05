<template>
  <!-- `contain`: fetched `position: fixed` styles cannot cover the portal. -->
  <div
    class="flex min-h-0 w-full flex-1 flex-row overflow-y-hidden [contain:paint]"
  >
    <PortalDocsSidebar :related="page?.related" :site-url="siteUrl" />
    <div
      ref="panel"
      class="relative grid h-full min-w-0 flex-1 grid-cols-1 content-start items-start overflow-y-auto pt-6 sm:pt-10 xl:grid-cols-[minmax(24px,1fr)_minmax(0,700px)_minmax(24px,1fr)_300px] xl:pe-4"
    >
      <RouterLink
        :to="ROUTES.home"
        class="mx-auto mb-4 flex w-full max-w-[700px] items-center gap-2 px-4 text-base text-ink-gray-6 sm:px-6 md:hidden"
      >
        <span class="lucide-arrow-left size-4 shrink-0" />
        {{ __("Help center") }}
      </RouterLink>

      <div
        v-if="failed"
        class="flex flex-col items-center self-stretch pb-16 xl:col-span-4"
      >
        <PortalEmptyState
          :title="__('Page not found')"
          :description="
            __('It may have moved, or you may need to sign in to read it.')
          "
        />
        <a
          :href="sourceUrl"
          target="_blank"
          rel="noopener"
          class="text-base text-ink-gray-7 underline"
        >
          {{ __("View on {0}", [host]) }}
        </a>
      </div>

      <PortalSkeleton
        v-else-if="!page"
        variant="article"
        class="mx-auto flex w-full min-w-0 max-w-[700px] flex-col px-4 sm:px-6 xl:col-start-2 xl:px-0"
      />

      <template v-else>
        <div
          class="portal-reveal mx-auto flex min-h-full w-full min-w-0 max-w-[700px] flex-col gap-6 px-4 pb-16 sm:px-6 xl:col-start-2 xl:px-0"
        >
          <div
            class="flex w-full flex-col gap-3 border-b border-outline-gray-1 pb-3.5"
          >
            <h1 class="min-w-0 text-4xl-semibold text-ink-gray-9 max-sm:!text-[24px]">
              {{ page.title }}
            </h1>
            <div
              class="flex flex-wrap items-center gap-x-2 text-sm text-ink-gray-5"
            >
              <span>{{ page.label }}</span>
              <template v-if="page.last_updated">
                <span>·</span>
                <span>{{ __("Updated {0}", [page.last_updated]) }}</span>
              </template>
              <span>·</span>
              <a
                :href="sourceUrl"
                target="_blank"
                rel="noopener"
                class="underline"
              >
                {{ __("View on {0}", [host]) }}
              </a>
            </div>
            <div v-if="session.isAgent.value" class="flex flex-wrap items-center gap-2">
              <a
                v-if="page.converted"
                :href="articleHref(page.converted.name)"
                target="_blank"
                rel="noopener"
                class="text-base text-ink-gray-7 underline"
              >
                {{ page.converted.title }}
              </a>
              <Button
                v-else
                :label="__('Convert to article')"
                @click="showConvert = true"
              />
            </div>
          </div>
          <DocsConvertDialog
            v-model:open="showConvert"
            :routes="[page.route]"
            :matching="page.matching"
            @done="(name) => (page.converted = { name, title: page.title })"
          />
          <PortalTableOfContents
            v-if="parsed.toc.length > 1"
            :items="parsed.toc"
            collapsible
            class="w-full xl:hidden"
          />
          <PortalArticleBody :content="parsed.html" class="flex-1" />
        </div>
        <div
          class="sticky top-0 hidden w-[300px] flex-col self-start pb-4 pr-3 xl:col-start-4 xl:flex"
        >
          <PortalTableOfContents :items="parsed.toc" class="w-full" />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch, watchEffect } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { Button, frappeRequest } from "frappe-ui";
import DocsConvertDialog from "@helpdesk/shared/settings/DocsConvertDialog.vue";
import { articleHref } from "@helpdesk/shared/settings/docsLinks";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { __ } from "@helpdesk/shared/translation";
import { addHeadingIds } from "@helpdesk/shared/utils";
import PortalArticleBody from "@app/components/knowledge_base/PortalArticleBody.vue";
import PortalDocsSidebar from "@app/components/knowledge_base/PortalDocsSidebar.vue";
import PortalTableOfContents from "@app/components/knowledge_base/PortalTableOfContents.vue";
import PortalEmptyState from "@app/components/ui/PortalEmptyState.vue";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";
import { scrollToHash } from "@app/stores/knowledgeBase";
import { useSession } from "@app/stores/session";

const props = defineProps<{ route: string }>();

const router = useRouter();
const session = useSession();
const panel = ref<HTMLElement | null>(null);
const page = ref<any>(null);
const failed = ref(false);
const showConvert = ref(false);

const docsUrl = computed<string>(() => session.config.value.docs_source_url);
const siteUrl = computed(() => page.value?.site_url || docsUrl.value);
const sourceUrl = computed(
  () => page.value?.source_url || `${docsUrl.value}/${props.route}`,
);
const host = computed(() => new URL(sourceUrl.value).host);

const parsed = computed(() => {
  const { html, headings } = addHeadingIds(page.value?.content);
  return { html, toc: headings.filter((heading) => heading.level <= 3) };
});

watch(() => props.route, load, { immediate: true });

async function load(route: string) {
  page.value = null;
  failed.value = false;
  try {
    const data = await frappeRequest({
      url: "helpdesk.api.docs_source.get_doc_page",
      method: "GET",
      params: { route },
    });
    // `panel` is gone once the reader left the page.
    if (route !== props.route || !panel.value) return;
    if (data.article) return router.replace(ROUTES.article(data.article));
    page.value = data;
    await nextTick();
    if (location.hash) scrollToHash();
    else panel.value?.scrollTo({ top: 0 });
  } catch {
    if (route === props.route) failed.value = true;
  }
}

// Same as the Article's `tab_title`.
watchEffect(() => {
  if (page.value) document.title = `${page.value.title} | ${session.brandName.value}`;
});

// Each run replaces the last page's tags; unmount removes them.
watchEffect((onCleanup) => {
  if (!page.value) return;
  const robots = Object.assign(document.createElement("meta"), {
    name: "robots",
    content: "noindex",
  });
  const canonical = Object.assign(document.createElement("link"), {
    rel: "canonical",
    href: page.value.source_url,
  });
  document.head.append(robots, canonical);
  onCleanup(() => {
    robots.remove();
    canonical.remove();
  });
});
</script>
