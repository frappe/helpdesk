function helpdesk_handlers(socket) {
  socket.on("ping", () => {
    socket.emit("pong");
  });

  socket.on("view_ticket", (ticket_id) => {
    if (!ticket_id || !socket.user) return;
    const room = open_doc_room("HD Ticket", ticket_id);
    socket.join(room);

    // Notify all viewers in this ticket room about the new viewer
    notify_ticket_viewers({
      socket: socket,
      ticket_id: ticket_id,
    });
  });

  socket.on("stop_view_ticket", (ticket_id) => {
    if (!ticket_id || !socket.user) return;
    const room = open_doc_room("HD Ticket", ticket_id);
    socket.leave(room);

    // Notify remaining viewers that someone left
    notify_ticket_viewers({
      socket: socket,
      ticket_id: ticket_id,
    });
  });

  socket.on("ticket_get_viewers", (ticket_id) => {
    if (!ticket_id || !socket.user) return;
    // Send current viewers list to the requesting user only
    notify_ticket_viewers({
      socket: socket,
      ticket_id: ticket_id,
      toUser: true,
    });
  });

  socket.on("notify_ticket_update", (ticket_id, field, value) => {
    if (!(ticket_id && field && socket.user)) return;

    // Only broadcast if the user is actually in the ticket room
    const ticket_room = open_doc_room("HD Ticket", ticket_id);
    const rooms = socket.rooms;
    if (!rooms.has(ticket_room)) return;

    socket.to(ticket_room).emit("ticket_update", {
      ticket_id,
      user: socket.user,
      field,
      value,
    });
  });

  // Typing indicators
  socket.on("helpdesk_ticket_typing", (ticket_id) => {
    if (!ticket_id || !socket.user) return;
    const ticket_room = open_doc_room("HD Ticket", ticket_id);

    // Only broadcast if the user is in the ticket room
    if (!socket.rooms.has(ticket_room)) return;

    socket.to(ticket_room).emit("helpdesk_ticket_typing", {
      ticket_id,
      user: socket.user,
    });
  });

  socket.on("helpdesk_ticket_typing_stopped", (ticket_id) => {
    if (!ticket_id || !socket.user) return;
    const ticket_room = open_doc_room("HD Ticket", ticket_id);

    // Only broadcast if the user is in the ticket room
    if (!socket.rooms.has(ticket_room)) return;

    socket.to(ticket_room).emit("helpdesk_ticket_typing_stopped", {
      ticket_id,
      user: socket.user,
    });
  });
}

function notify_ticket_viewers(args) {
  if (!(args && args.socket && args.ticket_id)) return;

  const socket = args.socket;
  const ticket_id = args.ticket_id;

  const ticket_room = open_doc_room("HD Ticket", ticket_id);

  const clients = Array.from(socket.nsp.adapter.rooms.get(ticket_room) || []);

  let users = [];

  // Extract user information for each socket in the room
  socket.nsp.sockets.forEach((sock) => {
    if (clients.includes(sock.id) && sock.user) {
      users.push(sock.user);
    }
  });

  const uniqueUsers = Array.from(new Set(users));

  const target_room = args.toUser
    ? user_room(args.socket.user) // Send to specific user only
    : ticket_room; // Send to all viewers in the ticket room

  // Emit the notification with current viewers list
  socket.nsp.to(target_room).emit("ticket_viewers", {
    ticket_id,
    users: JSON.stringify(uniqueUsers),
    total_viewers: uniqueUsers.length,
  });
}

// Helper functions
const open_doc_room = (doctype, docname) =>
  "open_doc:" + doctype + "/" + docname;
const user_room = (user) => "user:" + user;

module.exports = helpdesk_handlers;
