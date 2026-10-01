import { __ } from "@/translation";
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
  "Image",
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
    label: __("Email"),
    value: "email",
  },
  {
    label: __("First Name"),
    value: "first_name",
  },
  {
    label: __("Middle Name"),
    value: "middle_name",
  },
  {
    label: __("Last Name"),
    value: "last_name",
  },
  {
    label: __("Full Name"),
    value: "full_name",
  },
  {
    label: __("Username"),
    value: "username",
  },
  {
    label: __("User Image"),
    value: "user_image",
  },
  {
    label: __("Phone"),
    value: "phone",
  },
  {
    label: __("Location"),
    value: "location",
  },
  {
    label: __("Bio"),
    value: "bio",
  },
  {
    label: __("Mobile No"),
    value: "mobile_no",
  },
];

export const activeFilter = ref("Personal");
