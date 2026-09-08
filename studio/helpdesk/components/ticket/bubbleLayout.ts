// The two thread layouts, as the style values the message blocks bind — Studio
// evaluates `baseStyles`, so a row carries its own geometry rather than the page
// forking into two templates. Presentation data, so it lives beside the ticket
// components rather than in the thread store that hands it out.

// Timeline is the default: every message in one column, hung off the rail.
export const TIMELINE = {
  // The face lives beside the card, never in it — the rail is its column.
  showRail: true,
  // Lined up with the first line of the card, which is the byline.
  avatarOffset: '6px',
  avatarLeft: '0px',
  rowDisplay: 'grid',
  rowDirection: 'row',
  // How far the row sits from the thread's own left edge. The timeline starts at it.
  rowLeft: '0px',
  contentAlign: 'stretch',
  // A record, not a bubble: the card takes the column and every message lines up.
  cardWidth: 'auto',
  cardMaxWidth: 'none',
  cardPadding: '10px 12px 8px',
  cardBackground: 'var(--surface-elevation-1)',
  cardBorder: '1px solid var(--outline-gray-2)',
}

// Chat drops the grid for a flex row, so the reader's own messages can turn around and
// sit against the other edge. A bubble is as wide as what was said and no wider: the frame
// inside reports the width its content wants (`hug` in KbEmailContent), so the card can
// shrink to it, and three quarters of the column is where a long message stops and wraps
// instead of running the width of the thread.
export const THEIR_BUBBLE = {
  ...TIMELINE,
  // Chat's byline sits above the bubble, so the face sits at the top of the row and shifts
  // in towards the name it belongs to.
  avatarOffset: '-4px',
  avatarLeft: '23px',
  rowDisplay: 'flex',
  contentAlign: 'flex-start',
  // Chat pulls an incoming row out past that edge, so the face — not the bubble — is what
  // lines up with everything else in the column.
  rowLeft: '-16px',
  cardWidth: 'fit-content',
  cardMaxWidth: '76%',
  cardPadding: '12px 16px 14px',
}

export const OWN_BUBBLE = {
  ...THEIR_BUBBLE,
  // Nobody needs their own face shown back at them: the side of the thread says whose it
  // is, so the bubble takes the whole width and sits flush against the edge.
  showRail: false,
  rowDirection: 'row-reverse',
  // Nothing hangs off the left of your own message, so it keeps to the edge.
  rowLeft: '0px',
  contentAlign: 'flex-end',
  // Tinted and borderless, the way every chat marks the side you are on.
  cardBackground: 'var(--surface-gray-1)',
  cardBorder: '1px solid transparent',
}

// How long a run of messages stays one turn, and how tightly those messages sit.
export const GROUP_SECONDS = 5 * 60
export const GROUPED_GAP = '12px'
export const ROW_GAP = '24px'

/** The layout values a row carries, by layout mode and whose message it is. */
export function layoutOf(isChat: boolean, isOwn: boolean) {
  if (!isChat) return TIMELINE
  return isOwn ? OWN_BUBBLE : THEIR_BUBBLE
}
