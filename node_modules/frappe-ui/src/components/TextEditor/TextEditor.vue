<template>
  <div class="relative w-full" :class="$attrs.class" v-if="editor">
    <BubbleMenu
      v-if="bubbleMenuButtons"
      class="bubble-menu"
      :tippy-options="{ duration: 100 }"
      :editor="editor"
    >
      <Menu
        :editor="editor"
        class="border border-gray-100 rounded-md shadow-sm"
        :buttons="bubbleMenuButtons"
      />
    </BubbleMenu>

    <Menu
      v-if="fixedMenuButtons"
      class="w-full border rounded-t-lg border-gray-50 border-b-gray-100"
      :editor="editor"
      :buttons="fixedMenuButtons"
    />

    <FloatingMenu
      v-if="floatingMenuButtons"
      :tippy-options="{ duration: 100 }"
      :editor="editor"
      class="flex"
    >
      <button
        v-for="button in floatingMenuButtons"
        :key="button.label"
        class="flex p-1 text-gray-800 transition-colors rounded"
        :class="button.isActive(editor) ? 'bg-gray-100' : 'hover:bg-gray-100'"
        @click="() => button.action(editor)"
        :title="button.label"
      >
        <FeatherIcon v-if="button.icon" :name="button.icon" class="w-4" />
        <span class="inline-block h-4 text-sm leading-4 min-w-[1rem]" v-else>
          {{ button.text }}
        </span>
      </button>
    </FloatingMenu>
    <editor-content :editor="editor" />
  </div>
</template>

<script>
import { Editor, EditorContent, BubbleMenu, FloatingMenu } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Image from '@tiptap/extension-image'
import Menu from './Menu.vue'
import commands from './commands'

export default {
  name: 'TextEditor',
  inheritAttrs: false,
  components: {
    EditorContent,
    BubbleMenu,
    FloatingMenu,
    Menu,
  },
  props: [
    'content',
    'placeholder',
    'editorClass',
    'fixedMenu',
    'bubbleMenu',
    'floatingMenu',
    'extensions',
  ],
  emits: ['change'],
  expose: ['editor'],
  data() {
    return {
      editor: null,
    }
  },
  mounted() {
    this.editor = new Editor({
      content: this.content || '<p></p>',
      editorProps: {
        attributes: {
          class: ['prose prose-sm prose-p:my-1', this.editorClass].join(' '),
        },
      },
      extensions: [
        StarterKit,
        Image,
        Placeholder.configure({
          placeholder: this.placeholder || 'Write something...',
        }),
        ...(this.extensions || []),
      ],
      onUpdate: ({ editor }) => {
        this.$emit('change', editor.getHTML())
      },
    })
  },
  beforeUnmount() {
    this.editor.destroy()
  },
  computed: {
    fixedMenuButtons() {
      if (!this.fixedMenu) return false

      let buttons
      if (Array.isArray(this.fixedMenu)) {
        buttons = this.fixedMenu
      } else {
        buttons = [
          'Paragraph',
          'Heading 2',
          'Heading 3',
          'Separator',
          'Bold',
          'Italic',
          'Separator',
          'Bullet List',
          'Numbered List',
          'Blockquote',
          'Code',
          'Horizontal Rule',
          'Separator',
          'Undo',
          'Redo',
        ]
      }
      return buttons.map(createEditorButton)
    },
    bubbleMenuButtons() {
      if (!this.bubbleMenu) return false

      let buttons
      if (Array.isArray(this.bubbleMenu)) {
        buttons = this.bubbleMenu
      } else {
        buttons = [
          'Paragraph',
          'Heading 2',
          'Heading 3',
          'Separator',
          'Bold',
          'Italic',
          'Separator',
          'Bullet List',
          'Numbered List',
          'Blockquote',
          'Code',
        ]
      }
      return buttons.map(createEditorButton)
    },
    floatingMenuButtons() {
      if (!this.floatingMenu) return false

      let buttons
      if (Array.isArray(this.floatingMenu)) {
        buttons = this.floatingMenu
      } else {
        buttons = [
          'Paragraph',
          'Heading 2',
          'Heading 3',
          'Bullet List',
          'Numbered List',
          'Blockquote',
          'Code',
          'Horizontal Rule',
        ]
      }
      return buttons.map(createEditorButton)
    },
  },
}

function createEditorButton(option) {
  if (typeof option == 'object') {
    return option
  }
  return commands[option]
}
</script>
<style>
.ProseMirror:not(.ProseMirror-focused) p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  float: left;
  color: theme('colors.gray.500');
  pointer-events: none;
  height: 0;
}
</style>
