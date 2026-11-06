/** The first-ticket check runs until a ticket arrives, and not while the tab is hidden. */
export const shouldPoll = (state: { arrived: boolean; hidden: boolean }) =>
  !state.arrived && !state.hidden;
