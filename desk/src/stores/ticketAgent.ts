import { defineStore } from "pinia";
import { ref } from "vue";
import { createResource } from "frappe-ui";

export const useTicketAgentStore = defineStore("ticketAgent", () => {
  const assignees = ref([]);

  function getAssignees() {
    return assignees.value;
  }

  function updateAssignees(newAssignees) {
    console.log("updateAssignee", newAssignees);
  }

  function getTicket(ticketId) {
    const ticket = createResource({
      url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
      cache: ["Ticket", ticketId],
      auto: true,
      params: {
        name: ticketId,
      },
      onSuccess: (data) => {
        assignees.value = [
          {
            name: data.assignee.email,
            image: data.assignee.image,
            label: data.assignee.name,
          },
        ];
      },
    });

    return ticket;
  }

  return {
    updateAssignees,
    getAssignees,
    getTicket,
  };
});
