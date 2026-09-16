// Style values the message blocks bind, so a row carries its own geometry rather than
// the page forking into two templates.

export const TIMELINE = {
  showRail: true,
  // Lined up with the first line of the card, which is the byline.
  avatarOffset: '6px',
  avatarLeft: '0px',
  rowDisplay: 'grid',
  rowDirection: 'row',
  // How far the row sits from the thread's own left edge.
  rowLeft: '0px',
  contentAlign: 'stretch',
  cardWidth: 'auto',
  cardMaxWidth: 'none',
  cardPadding: '10px 12px 8px',
  cardBackground: 'var(--surface-elevation-1)',
  cardBorder: '1px solid var(--outline-gray-2)',
}

// A flex row, so the reader's own messages can turn around and sit against the other edge.
// The card shrinks to the width `hug` in KbEmailContent reports, capped at three quarters.
export const THEIR_BUBBLE = {
  ...TIMELINE,
  // The byline sits above the bubble, so the face shifts in towards the name.
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

export const OWN_BUBBLE = {
  ...THEIR_BUBBLE,
  // The side of the thread already says whose it is, so no face is shown back at you.
  showRail: false,
  rowDirection: 'row-reverse',
  rowLeft: '0px',
  contentAlign: 'flex-end',
  cardBackground: 'var(--surface-gray-1)',
  cardBorder: '1px solid transparent',
}

// How long a run of messages stays one turn, and how tightly those messages sit.
export const GROUP_SECONDS = 5 * 60
export const GROUPED_GAP = '12px'
export const ROW_GAP = '24px'

export function layoutOf(isChat: boolean, isOwn: boolean) {
  if (!isChat) return TIMELINE
  return isOwn ? OWN_BUBBLE : THEIR_BUBBLE
}
