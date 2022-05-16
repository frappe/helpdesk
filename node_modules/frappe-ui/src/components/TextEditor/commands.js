export default {
  Paragraph: {
    label: 'Paragraph',
    icon: 'type',
    action: (editor) => editor.chain().focus().setParagraph().run(),
    isActive: (editor) => editor.isActive('paragraph'),
  },
  'Heading 2': {
    label: 'Heading 2',
    text: 'H2',
    action: (editor) =>
      editor.chain().focus().toggleHeading({ level: 2 }).run(),
    isActive: (editor) => editor.isActive('heading', { level: 2 }),
  },
  'Heading 3': {
    label: 'Heading 3',
    text: 'H3',
    action: (editor) =>
      editor.chain().focus().toggleHeading({ level: 3 }).run(),
    isActive: (editor) => editor.isActive('heading', { level: 3 }),
  },
  Bold: {
    label: 'Bold',
    icon: 'bold',
    action: (editor) => editor.chain().focus().toggleBold().run(),
    isActive: (editor) => editor.isActive('bold'),
  },
  Italic: {
    label: 'Italic',
    icon: 'italic',
    action: (editor) => editor.chain().focus().toggleItalic().run(),
    isActive: (editor) => editor.isActive('italic'),
  },
  'Bullet List': {
    label: 'Bullet List',
    icon: 'list',
    action: (editor) => editor.chain().focus().toggleBulletList().run(),
    isActive: (editor) => editor.isActive('bulletList'),
  },
  'Numbered List': {
    label: 'Numbered List',
    text: '1.',
    action: (editor) => editor.chain().focus().toggleOrderedList().run(),
    isActive: (editor) => editor.isActive('orderedList'),
  },
  Blockquote: {
    label: 'Blockquote',
    icon: 'chevron-right',
    action: (editor) => editor.chain().focus().toggleBlockquote().run(),
    isActive: (editor) => editor.isActive('blockquote'),
  },
  Code: {
    label: 'Code',
    icon: 'code',
    action: (editor) => editor.chain().focus().toggleCodeBlock().run(),
    isActive: (editor) => editor.isActive('codeBlock'),
  },
  'Horizontal Rule': {
    label: 'Horizontal Rule',
    icon: 'minus',
    action: (editor) => editor.chain().focus().setHorizontalRule().run(),
    isActive: (editor) => false,
  },
  Undo: {
    label: 'Undo',
    icon: 'corner-up-left',
    action: (editor) => editor.chain().focus().undo().run(),
    isActive: (editor) => false,
  },
  Redo: {
    label: 'Redo',
    icon: 'corner-up-right',
    action: (editor) => editor.chain().focus().redo().run(),
    isActive: (editor) => false,
  },
  Separator: {
    type: 'separator',
  },
}
