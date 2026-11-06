// The preview is drawn on a fixed 640 stage, so lines and HTML stay aligned at any size.
export const STAGE = 640;
export const ENTRY_X = 356;

/** One strand of the ribbon from the mailbox to the ticket; `n` fans them apart. */
export const strandPath = (n: number) => {
  const i = n * 1.7;
  return (
    `M 76 74 C ${170 + i * 6} ${20 + i * 10}, ${250 + i * 10} ${130 + i * 12}, ${330 + i * 4} ${90 + i * 12} ` +
    `S ${ENTRY_X + 30 + i * 14} ${106 + i * 6}, ${ENTRY_X + i * 4} 196`
  );
};

// Where up to five agents sit below the ticket.
export const AGENT_SLOTS: [number, number][] = [
  [292, 552],
  [372, 586],
  [452, 572],
  [526, 530],
  [588, 466],
];

/** A root from under the ticket's lower edge to an agent at (x, y). */
export const rootPath = (x: number, y: number) => {
  const from = ENTRY_X + (x - 440) * 0.28;
  return `M ${from} 340 C ${from} ${340 + (y - 340) * 0.85}, ${from + (x - from) * 0.35} ${y + 10}, ${x} ${y}`;
};
