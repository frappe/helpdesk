#!/bin/bash
cat << 'INNER_EOF' > fix_app_vue.py
with open('desk/src/App.vue', 'r') as f:
    content = f.read()

content = content.replace("  { immediate: true },\n)", "  { immediate: true },\n);")
content = content.replace("  { immediate: true }\n)", "  { immediate: true },\n);")
content = content.replace('import("@/pages/desk/AgentRoot.vue")\n)', 'import("@/pages/desk/AgentRoot.vue"),\n);')
content = content.replace('import("@/pages/desk/AgentRoot.vue"),\n)', 'import("@/pages/desk/AgentRoot.vue"),\n);')
content = content.replace('import("@/pages/CustomerPortalRoot.vue")\n)', 'import("@/pages/CustomerPortalRoot.vue"),\n);')
content = content.replace('import("@/pages/CustomerPortalRoot.vue"),\n)', 'import("@/pages/CustomerPortalRoot.vue"),\n);')

with open('desk/src/App.vue', 'w') as f:
    f.write(content)
INNER_EOF
python3 fix_app_vue.py
rm fix_app_vue.py
