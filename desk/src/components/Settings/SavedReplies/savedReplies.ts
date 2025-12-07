import { ref } from "vue";

export const menuButtons = [
  [
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Heading 4",
    "Heading 5",
    "Heading 6",
  ],
  "Paragraph",
  "Separator",
  "Bold",
  "Italic",
  "Separator",
  "Bullet List",
  "Numbered List",
  "Task List",
  "Separator",
  "Align Left",
  "Align Center",
  "Align Right",
  "FontColor",
  "Separator",
  "Link",
  "Blockquote",
  "Code",
  "Horizontal Rule",
  [
    "InsertTable",
    "AddColumnBefore",
    "AddColumnAfter",
    "DeleteColumn",
    "AddRowBefore",
    "AddRowAfter",
    "DeleteRow",
    "MergeCells",
    "SplitCell",
    "ToggleHeaderColumn",
    "ToggleHeaderRow",
    "ToggleHeaderCell",
    "DeleteTable",
  ],
  "Separator",
  "Undo",
  "Redo",
];

export const userFields = [
  {
    label: "Email",
    value: "email",
  },
  {
    label: "First Name",
    value: "first_name",
  },
  {
    label: "Middle Name",
    value: "middle_name",
  },
  {
    label: "Last Name",
    value: "last_name",
  },
  {
    label: "Full Name",
    value: "full_name",
  },
  {
    label: "Username",
    value: "username",
  },
  {
    label: "User Image",
    value: "user_image",
  },
  {
    label: "Phone",
    value: "phone",
  },
  {
    label: "Location",
    value: "location",
  },
  {
    label: "Bio",
    value: "bio",
  },
  {
    label: "Mobile No",
    value: "mobile_no",
  },
];

export const activeFilter = ref("Personal");
