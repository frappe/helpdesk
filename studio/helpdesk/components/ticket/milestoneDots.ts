// Full literal strings: Tailwind's scanner cannot see interpolation.
export const MILESTONE_DOT_CLASSES = {
  done: 'size-2 bg-[var(--ink-green-6)]',
  closed: 'size-2 bg-[var(--outline-gray-4)]',
  next: 'size-2.5 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-amber-7)]',
  pending: 'size-2 bg-surface-base shadow-[inset_0_0_0_1.5px_var(--outline-gray-4)]',
}

export type MilestoneState = keyof typeof MILESTONE_DOT_CLASSES
