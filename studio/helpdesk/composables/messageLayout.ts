// Geometry the message blocks bind, so one template serves both layouts.

const TIMELINE = {
  showRail: true,
  avatarOffset: '6px',
  avatarLeft: '0px',
  rowDisplay: 'grid',
  rowDirection: 'row',
  rowLeft: '0px',
  contentAlign: 'stretch',
  cardWidth: 'auto',
  cardMaxWidth: 'none',
  cardPadding: '10px 12px 8px',
  cardBackground: 'var(--surface-elevation-1)',
  cardBorder: '1px solid var(--outline-gray-2)',
}

const THEIR_BUBBLE = {
  ...TIMELINE,
  avatarOffset: '-4px',
  avatarLeft: '23px',
  rowDisplay: 'flex',
  contentAlign: 'flex-start',
  // Pulled out past the edge, so the face lines up with the column, not the bubble.
  rowLeft: '-16px',
  cardWidth: 'fit-content',
  cardMaxWidth: '76%',
  cardPadding: '12px 16px 14px',
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

export function layoutOf(isChat: boolean, isOwn: boolean) {
  if (!isChat) return TIMELINE
  return isOwn ? OWN_BUBBLE : THEIR_BUBBLE
}
