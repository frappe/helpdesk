import type { Ref } from "vue";
import { __ } from "../translation";
import { ConfirmDelete } from "../utils";

export const DRAG_OPTIONS = {
  animation: 150,
  delay: 200,
  delayOnTouchOnly: true,
  ghostClass: "opacity-40",
};

export function moveItem(list: unknown[], from: number, to: number) {
  list.splice(to, 0, ...list.splice(from, 1));
}

/** Move up, Move down and Delete (or `remove`) for row `index`; each sets a new list. */
export function rowOptions<T>(
  items: Ref<T[]>,
  index: number,
  isConfirmingDelete: Ref<boolean>,
  remove?: { label: string; icon: string }
) {
  const update = (change: (list: T[]) => void) => {
    const list = [...items.value];
    change(list);
    items.value = list;
  };
  const moveTo = (to: number) => update((list) => moveItem(list, index, to));
  const removeItem = () => update((list) => list.splice(index, 1));
  return [
    {
      label: __("Move up"),
      icon: "lucide-arrow-up",
      disabled: index === 0,
      onClick: () => moveTo(index - 1),
    },
    {
      label: __("Move down"),
      icon: "lucide-arrow-down",
      disabled: index === items.value.length - 1,
      onClick: () => moveTo(index + 1),
    },
    ...(remove
      ? [{ ...remove, onClick: removeItem }]
      : ConfirmDelete({ isConfirmingDelete, onConfirmDelete: removeItem })),
  ];
}
