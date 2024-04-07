import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { createResource, call } from "frappe-ui";
import { createToast } from "@/utils";

export const useTicketAgentStore = defineStore("ticketAgent", () => {
  const assignees = ref([]);
  let _ticketId;
  let _ticket;
  const showFullActivity = ref(true);

  function getAssignees() {
    return assignees.value;
  }

  function updateAssignees({ assigneesToRemove, newAssignees }) {
    for (const a of assigneesToRemove) {
      call("frappe.desk.form.assign_to.remove", {
        doctype: "HD Ticket",
        name: _ticketId,
        assign_to: a,
      });
    }

    if (newAssignees.length) {
      call("frappe.desk.form.assign_to.add", {
        doctype: "HD Ticket",
        name: _ticketId,
        assign_to: newAssignees,
      });
    }

    _ticket.reload();

    //TODO: promise.all, await, multiple assignees?
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

  const activities = computed(() => {
    const emailProps = _ticket.data.communications.map((email) => {
      return {
        type: "email",
        key: email.creation,
        sender: { name: email.user.email, full_name: email.user.name },
        to: email.recipients,
        cc: email.cc,
        bcc: email.bcc,
        creation: email.creation,
        subject: email.subject,
        attachments: email.attachments,
        content: email.content,
      };
    });

    const commentProps = _ticket.data.comments.map((comment) => {
      return {
        type: "comment",
        key: comment.creation,
        commenter: comment.user.name,
        creation: comment.creation,
        content: comment.content,
      };
    });

    if (!showFullActivity.value) {
      return [...emailProps, ...commentProps].sort(
        (a, b) => new Date(a.creation) - new Date(b.creation)
      );
    }

    const historyProps = [..._ticket.data.history, ..._ticket.data.views].map(
      (h) => {
        return {
          type: "history",
          key: h.creation,
          content: h.action ? h.action : "viewed this",
          creation: h.creation,
          user: h.user.name + " ",
        };
      }
    );

    const sorted = [...emailProps, ...commentProps, ...historyProps].sort(
      (a, b) => new Date(a.creation) - new Date(b.creation)
    );

    const data = [];
    let i = 0;

    while (i < sorted.length) {
      const currentActivity = sorted[i];
      if (currentActivity.type === "history") {
        currentActivity.relatedActivities = [];
        for (let j = i + 1; j < sorted.length; j++) {
          const nextActivity = sorted[j];
          if (nextActivity.type === "history") {
            currentActivity.relatedActivities.push(nextActivity);
          } else {
            data.push(currentActivity);
            i = j - 1;
            break;
          }
        }
      } else {
        data.push(currentActivity);
      }
      i++;
    }

    return data;
  });

  return {
    updateAssignees,
    getAssignees,
    getTicket,
    updateTicket,
    activities,
    showFullActivity,
  };
});
