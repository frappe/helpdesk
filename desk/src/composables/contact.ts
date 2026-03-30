import { __ } from "@/translation";
import { DocumentResource, Error } from "@/types";
import { Contact } from "@/types/doctypes";
import { call, toast } from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { ref } from "vue";

export function useContactInvite(doc: DocumentResource<Contact>) {
  const isLoading = ref(false);
  // @ts-expect-error
  const { updateOnboardingStep } = useOnboarding("helpdesk");
  async function inviteContact(): Promise<void> {
    try {
      isLoading.value = true;
      const user = await call(
        "frappe.contacts.doctype.contact.contact.invite_user",
        {
          contact: doc.doc.name,
        }
      );
      toast.success(__("Contact invited successfully"));
      await doc.setValue.submit({
        user: user,
      });
      updateOnboardingStep("add_invite_contact");
    } catch (error: unknown) {
      isLoading.value = false;
      const parser = new DOMParser();
      const doc = parser.parseFromString(
        (error as Error).messages?.[0] || (error as Error).message,
        "text/html"
      );

      const errMsg = doc.body.innerText;
      toast.error(errMsg);
    } finally {
      isLoading.value = false;
    }
  }
  return { inviteContact, isLoading };
}

export function useContactResetPassword(getUser: () => string | undefined) {
  const isLoading = ref(false);
  // /Users/ritviksardana/bench-dev/apps/frappe/frappe/core/doctype/user/user.py
  async function resetPassword(): Promise<void> {
    const user = getUser();
    console.log(user);
    if (!user) {
      toast.error(__("No system user is linked with this contact"));
      return;
    }
    try {
      isLoading.value = true;
      await call("frappe.core.doctype.user.user.reset_password", {
        user,
      });
      toast.success(__("Reset password email sent successfully"));
    } catch (error: unknown) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(
        (error as Error).messages?.[0] || (error as Error).message,
        "text/html"
      );

      const errMsg = doc.body.innerText;
      toast.error(errMsg);
    } finally {
      isLoading.value = false;
    }
  }
  return { resetPassword, isLoading };
}
