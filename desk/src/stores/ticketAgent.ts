import { defineStore } from "pinia";
import { ref } from "vue";
import { createResource } from "frappe-ui";
import { createToast } from "@/utils";

export const useTicketAgentStore = defineStore("ticketAgent", () => {
  const assignees = ref([]);
  let _ticketId;
  let _ticket;

  function getAssignees() {
    return assignees.value;
  }

  function updateAssignees(newAssignees) {
    console.log("updateAssignee", newAssignees);
  }

  function getTicket(ticketId) {
    _ticket = createResource({
      url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
      cache: ["Ticket", ticketId],
      auto: true,
      params: {
        name: ticketId,
      },
      onSuccess: (data) => {
        _ticketId = ticketId;
        assignees.value = [
          {
            name: data.assignee.email,
            image: data.assignee.image,
            label: data.assignee.name,
          },
        ];
      },
    });

    return _ticket;
  }

  function updateTicket(fieldname: string, value: string) {
    createResource({
      url: "frappe.client.set_value",
      params: {
        doctype: "HD Ticket",
        name: _ticketId,
        fieldname,
        value,
      },
      auto: true,
      onSuccess: () => {
        _ticket.reload();
        createToast({
          title: "Ticket updated",
          icon: "check",
          iconClasses: "text-green-600",
        });
      },
    });
  }

  return {
    updateAssignees,
    getAssignees,
    getTicket,
    updateTicket,
  };
});
