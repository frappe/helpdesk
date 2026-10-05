// Geometry the chat bubbles bind: theirs on the left beside a face, yours on the right.

const THEIR_BUBBLE = {
  showRail: true,
  avatarOffset: '-4px',
  avatarLeft: '23px',
  rowDisplay: 'flex',
  rowDirection: 'row',
  // Pulled out past the edge, so the face lines up with the column, not the bubble.
  rowLeft: '-16px',
  contentAlign: 'flex-start',
  cardWidth: 'fit-content',
  cardMaxWidth: '76%',
  cardPadding: '6px 12px',
  cardBackground: 'var(--surface-elevation-1)',
  cardBorder: '1px solid var(--outline-gray-2)',
}

const OWN_BUBBLE = {
  ...THEIR_BUBBLE,
  showRail: false,
  rowDirection: 'row-reverse',
  rowLeft: '0px',
  contentAlign: 'flex-end',
  cardBackground: 'var(--surface-gray-1)',
  cardBorder: '1px solid transparent',
}

export const GROUP_SECONDS = 5 * 60
export const GROUPED_GAP = '12px'
export const ROW_GAP = '24px'

// A phone has no gutter to pull the face into, and no width to leave beside a bubble.
const PHONE = { rowLeft: '0px', cardMaxWidth: '88%' }

export function bubbleLayout(isOwn: boolean, isPhone = false) {
  const layout = isOwn ? OWN_BUBBLE : THEIR_BUBBLE
  return isPhone ? { ...layout, ...PHONE } : layout
}
