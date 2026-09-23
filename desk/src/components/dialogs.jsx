import { Dialog, ErrorMessage } from "frappe-ui";
import { reactive, ref } from "vue";

let dialogs = ref([]);

export let Dialogs = {
  name: "Dialogs",
  render() {
    return dialogs.value.map((dialog) => (
      <Dialog
        title={dialog.title}
        size={dialog.size}
        icon={dialog.icon}
        position={dialog.position}
        actions={dialog.actions}
        open={dialog.show}
        onUpdate:open={(val) => (dialog.show = val)}
      >
        {{
          default: () => {
            return [
              dialog.message && (
                <p class="text-p-base text-ink-gray-7">{dialog.message}</p>
              ),
              dialog.html && <div v-html={dialog.html} />,
              <ErrorMessage class="mt-2" message={dialog.error} />,
            ];
          },
        }}
      </Dialog>
    ));
  },
};

// Callable context so form scripts written for `onClick(close)` keep working
// alongside frappe-ui v1's `onClick({ close })`.
function withLegacyCloseContext(actions) {
  return actions?.map((action) =>
    action.onClick
      ? {
          ...action,
          onClick: ({ close }) => {
            const context = () => close();
            context.close = close;
            return action.onClick(context);
          },
        }
      : action
  );
}

export function createDialog(dialogOptions) {
  let dialog = reactive(dialogOptions);
  dialog.actions = withLegacyCloseContext(dialog.actions);
  dialog.key = "dialog-" + dialogs.value.length;
  dialog.show = false;
  setTimeout(() => {
    dialog.show = true;
  }, 0);
  dialogs.value.push(dialog);
}
