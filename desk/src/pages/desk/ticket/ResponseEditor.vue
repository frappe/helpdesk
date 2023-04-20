<template>
	<div class="content mx-auto">
		<div class="my-3.5 ml-2 flex items-center gap-2 pl-2">
			<Avatar
				image-u-r-l="https://picsum.photos/200"
				label="foobar"
				size="md"
				class="self-start"
			/>
			<div
				v-if="!isActive"
				class="w-full rounded-lg border border-gray-300 py-2 px-2.5 text-base text-gray-500"
			>
				Type a reply / comment
			</div>
			<div v-if="isActive" class="editor-shadow grow">
				<TextEditor
					editor-class="prose-sm max-w-none p-3 overflow-auto h-32 focus:outline-none"
					:mentions="mentions"
					placeholder="Foobar"
				>
					<template #top>
						<div class="divide-y rounded-t-xl border-b">
							<div class="px-3.5 py-1.5 text-base">
								<div class="flex justify-between">
									<div class="flex items-center gap-4">
										<div class="text-gray-600">To:</div>
										<div
											class="flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-sm text-gray-800"
										>
											<Avatar
												image-u-r-l="https://picsum.photos/200"
												label="foobar"
												size="sm"
											/>
											hello@example.com
										</div>
									</div>
									<div class="flex gap-2">
										<div
											class="rounded-md bg-gray-300 px-2 py-1 text-base text-gray-800"
										>
											Cc
										</div>
										<div
											class="rounded-md bg-gray-300 px-2 py-1 text-base text-gray-800"
										>
											Bcc
										</div>
									</div>
								</div>
							</div>
							<div class="px-3.5 py-1.5 text-base">
								<div class="flex items-center gap-4">
									<div class="text-gray-600">Cc:</div>
									<div
										class="flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-sm text-gray-800"
									>
										<Avatar
											image-u-r-l="https://picsum.photos/200"
											label="foobar"
											size="sm"
										/>
										hello@example.com
									</div>
								</div>
							</div>
						</div>
					</template>
					<template #editor="{ editor }">
						<TextEditorContent :editor="editor" />
					</template>
					<template #bottom>
						<div class="flex flex-col divide-y rounded-b-xl">
							<div class="px-3.5 py-2">
								<TextEditorFixedMenu :buttons="menuButtons" />
							</div>
							<div class="flex justify-between px-3.5 py-2">
								<div class="flex flex-row items-center space-x-2">
									<FileUploader @success="(file) => attachments.push(file)">
										<template #default="{ uploading, openFileSelector }">
											<FeatherIcon
												name="paperclip"
												class="h-[17px]"
												role="button"
												:disabled="uploading"
												@click="openFileSelector"
											/>
										</template>
									</FileUploader>
									<CustomIcons
										name="add-response"
										class="h-7 w-7 rounded p-1"
										role="button"
										@click="
											() => {
												showCannedResponsesDialog = true;
											}
										"
									/>
									<CustomIcons
										name="article-reply"
										class="h-7 w-7 rounded p-1"
										role="button"
										@click="
											() => {
												showArticleResponseDialog = true;
											}
										"
									/>
									<CannedResponsesDialog
										:show="showCannedResponsesDialog"
										@close="
											() => {
												showCannedResponsesDialog = false;
											}
										"
									/>

									<ArticleResponseDialog
										:show="showArticleResponseDialog"
										@close="
											() => {
												showArticleResponseDialog = false;
											}
										"
									/>
								</div>
								<Button label="Reply" appearance="primary" />
							</div>
						</div>
					</template>
				</TextEditor>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import {
	Avatar,
	Button,
	FeatherIcon,
	FileUploader,
	TextEditor,
	TextEditorContent,
	TextEditorFixedMenu,
} from "frappe-ui";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";
import { TextEditorMenuButtons as menuButtons } from "../consts";

const attachments = ref([]);
const isActive = ref(true);
const showCannedResponsesDialog = ref(false);
const showArticleResponseDialog = ref(false);

const mentions = [
	{ label: "Husain Wrenn", value: "hwrenn0@spotify.com" },
	{ label: "Gwenore Fitter", value: "gfitter1@foxnews.com" },
	{ label: "Ricard Claussen", value: "rclaussen2@imgur.com" },
	{ label: "Rickard Higford", value: "rhigford3@multiply.com" },
	{ label: "Lazarus MacKey", value: "lmackey4@prlog.org" },
	{ label: "Karrah Ege", value: "kege5@prweb.com" },
	{ label: "Seward Godin", value: "sgodin6@msu.edu" },
	{ label: "Milzie Sanches", value: "msanches7@senate.gov" },
	{ label: "Walt Arrington", value: "warrington8@tripod.com" },
	{ label: "Seline Bonifas", value: "sbonifas9@hibu.com" },
];
</script>

<style scoped>
.content {
	width: 742px;
}

.editor-shadow {
	box-shadow: 0px 0px 1px rgba(0, 0, 0, 0.45), 0px 1px 2px rgba(0, 0, 0, 0.1);
	border-radius: 12px;
}
</style>
