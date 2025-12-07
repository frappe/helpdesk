<template>
  <div class="flex flex-col h-full">
    <div class="my-3 flex items-center justify-between text-lg font-medium sm:mb-4 sm:mt-8 px-3 sm:px-10">
      <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
        {{ __('Order Details') }}
      </div>
    </div>
    <div
      v-if="isLoading || fetching"
      class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-6"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span>{{ __('Loading...') }}</span>
    </div>
    <div v-else class="pb-8 px-3 sm:px-10">
      <div v-if="orderHistory.length > 0" class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="border-b">
              <th class="text-left p-3 font-semibold">Sales Order</th>
              <th class="text-left p-3 font-semibold">Order Date</th>
              <th class="text-left p-3 font-semibold item-code-header">Item Code</th>
              <th class="text-left p-3 font-semibold">Item Name</th>
              <th class="text-right p-3 font-semibold">Qty</th>
              <th class="text-right p-3 font-semibold rate-header">Rate</th>
              <th class="text-right p-3 font-semibold">Amount</th>
              <th class="text-left p-3 font-semibold">QA Status</th>
              <th class="text-left p-3 font-semibold">OPS Status</th>
              <th class="text-left p-3 font-semibold">Material Status</th>
              <th class="text-left p-3 font-semibold">Production Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, idx) in orderHistory"
              :key="idx"
              class="border-b hover:bg-gray-50"
            >
              <td class="p-3">
                <a
                  v-if="item.sales_order"
                  :href="`/app/sales-order/${item.sales_order}`"
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                >
                  {{ item.sales_order }}
                </a>
                <span v-else>-</span>
              </td>
              <td class="p-3">{{ item.order_date || '-' }}</td>
              <td class="p-3 item-code-cell">{{ item.item_code || '-' }}</td>
              <td class="p-3">{{ item.item_name || '-' }}</td>
              <td class="p-3 text-right">{{ item.qty || 0 }}</td>
              <td class="p-3 text-right rate-cell">{{ item.rate || 0 }}</td>
              <td class="p-3 text-right">{{ item.amount || 0 }}</td>
              <td class="p-3">
                <span v-if="item.qa_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(item.qa_status)">
                  {{ getStatusIcon(item.qa_status) }} {{ item.qa_status }}
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>
              <td class="p-3">
                <span v-if="item.ops_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(item.ops_status)">
                  {{ getStatusIcon(item.ops_status) }} {{ item.ops_status }}
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>
              <td class="p-3">
                <span v-if="item.mat_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(item.mat_status)">
                  {{ getStatusIcon(item.mat_status) }} {{ item.mat_status }}
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>
              <td class="p-3">
                <span v-if="item.pro_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(item.pro_status)">
                  {{ getStatusIcon(item.pro_status) }} {{ item.pro_status }}
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div
        v-else
        class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-4 py-8"
      >
        <span>{{ __('No order history found.') }}</span>
        <span v-if="!contactName" class="text-sm text-ink-gray-5">
          {{ __('Please set a Contact on this ticket to fetch order history.') }}
        </span>
        <span v-else-if="hasFetched && !fetching" class="text-sm text-ink-gray-5">
          {{ __('No orders found for this customer. Check browser console (F12) for details.') }}
        </span>
        <span v-else-if="fetching" class="text-sm text-ink-gray-5">
          {{ __('Fetching order history...') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { call, toast, LoadingIndicator } from "frappe-ui";
import { ref, inject, computed, onMounted, watch } from "vue";
import { ITicket } from "@/pages/ticket/symbols";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const ticket = inject(ITicket, null);
const fetching = ref(false);
const hasFetched = ref(false);

// Debug: Check if ticket is injected properly - log immediately
console.log('🔍 TicketOrderDetails - Injection check:', { 
  hasTicket: !!ticket, 
  ticketType: typeof ticket,
  ticketData: ticket?.data,
  ticketDataType: typeof ticket?.data,
  hasData: !!ticket?.data,
  ticketLoading: ticket?.loading,
  ticketResource: ticket
});

if (!ticket) {
  console.error('❌ ITicket not injected! Component may not be inside TicketAgent.');
} else {
  console.log('✅ ITicket injected successfully');
}

// Computed property to check if ticket is loading
const isLoading = computed(() => {
  if (!ticket) {
    console.warn('⚠️ isLoading: ticket is null');
    return true; // Show loading if ticket not injected
  }
  const loading = fetching.value || (ticket?.loading && !ticket?.data);
  console.log('⏳ isLoading computed:', { 
    fetching: fetching.value, 
    ticketLoading: ticket?.loading, 
    hasData: !!ticket?.data, 
    ticketData: ticket?.data,
    result: loading 
  });
  return loading;
});

// Computed property for order history
const orderHistory = computed(() => {
  return ticket?.data?.custom_order_history || [];
});

// Helper function to truncate duplicated contact names (e.g., "Tamala Fowler-Tamala Fowler" -> "Tamala Fowler")
function truncateContactName(name: string | undefined | null): string | null {
  if (!name) return null;
  if (name.includes('-')) {
    const parts = name.split('-');
    if (parts.length === 2 && parts[0].trim() === parts[1].trim()) {
      return parts[0].trim();
    }
  }
  return name;
}

// Computed property for contact name
const contactName = computed(() => {
  if (!ticket) {
    console.warn('⚠️ contactName: ticket is null');
    return null;
  }
  const contact = ticket?.data?.contact;
  const rawName = contact?.name || contact;
  const name = truncateContactName(rawName);
  console.log('👤 contactName computed:', { 
    hasTicket: !!ticket,
    ticketData: ticket?.data,
    contact, 
    rawName, 
    name 
  });
  return name;
});

// Status badge helper functions - EXACT match to ERPNext script
function getStatusColor(status: string | null | undefined): string {
  if (!status) return 'gray'
  const statusUpper = String(status).toUpperCase().trim()
  
  // Green - Complete/Approved
  if (['APPROVED', 'IN_STOCK', 'DONE', 'PASS'].includes(statusUpper)) {
    return 'green'
  }
  
  // Blue - Active/In Progress
  if (['WIP', 'IN PROGRESS', 'CONFIRMATION PENDING'].includes(statusUpper)) {
    return 'blue'
  }
  
  // Yellow - Warning/Review/Pending
  if (['NEW', 'AWAITING', 'REVIEW_REQUIRED', 'IN_STOCK_TENTATIVE', 
       'OPS REVIEW', 'EXPECTED', 'QA REWORK', 'ALTERNATE FABRIC', 
       'BLOCK REVIEW', 'NO RECIPE', 'NOT STARTED', 'NO_RECIPE'].includes(statusUpper)) {
    return 'yellow'
  }
  
  // Red - Error/Blocked/Not Available
  if (['NOT_AVAILABLE', 'NOT AVAILABLE', 'BLOCKED_FACTORY', 'BLOCKED_OPS', 
       'FAIL', 'CANCEL REQUEST', 'POST APPROVAL HOLD OR CHANGE REQUEST', 
       'PRE_APPROVAL_CUSTOMER HOLD'].includes(statusUpper)) {
    return 'red'
  }
  
  // Gray - Default
  return 'gray'
}

function getStatusIcon(status: string | null | undefined): string {
  if (!status) return '📋'
  const statusUpper = String(status).toUpperCase().trim()
  
  const iconMap: Record<string, string> = {
    'APPROVED': '✅',
    'IN_STOCK': '✅',
    'DONE': '✅',
    'PASS': '✅',
    'WIP': '⚙️',
    'IN PROGRESS': '🔍',
    'NEW': '🆕',
    'AWAITING': '⏳',
    'REVIEW_REQUIRED': '⚠️',
    'OPS REVIEW': '👀',
    'NOT_AVAILABLE': '🔴',
    'NOT AVAILABLE': '🔴',
    'BLOCKED_FACTORY': '🚧',
    'BLOCKED_OPS': '⚠️',
    'FAIL': '❌',
    'EXPECTED': '📦',
    'NO RECIPE': '📝',
    'NO_RECIPE': '📝',
    'NOT STARTED': '🔵',
    'QA REWORK': '🔄'
  }
  
  return iconMap[statusUpper] || '📋'
}

onMounted(() => {
  // Add status badge styles - EXACT match to ERPNext script
  if (!document.getElementById('crm-status-badge-styles')) {
    const styles = document.createElement('style')
    styles.id = 'crm-status-badge-styles'
    styles.textContent = `
      .status-badge-crm {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        white-space: nowrap;
        border: 1px solid;
      }
      .status-badge-green {
        background: #ecfdf5;
        color: #059669;
        border-color: #a7f3d0;
      }
      .status-badge-blue {
        background: #eff6ff;
        color: #2563eb;
        border-color: #bfdbfe;
      }
      .status-badge-yellow {
        background: #fffbeb;
        color: #d97706;
        border-color: #fde68a;
      }
      .status-badge-red {
        background: #fef2f2;
        color: #dc2626;
        border-color: #fecaca;
      }
      .status-badge-gray {
        background: #f9fafb;
        color: #6b7280;
        border-color: #e5e7eb;
      }
      /* Hide Item Code and Rate columns */
      .item-code-header,
      .item-code-cell,
      .rate-header,
      .rate-cell {
        display: none !important;
      }
    `
    document.head.appendChild(styles)
  }

  // Reset fetch flag when component mounts (so it fetches every time tab is clicked)
  hasFetched.value = false;
  
  console.log('🚀 TicketOrderDetails onMounted', { 
    ticketId: props.ticketId, 
    hasTicket: !!ticket,
    ticketData: ticket?.data,
    hasData: !!ticket?.data,
    contact: ticket?.data?.contact,
    ticketLoading: ticket?.loading,
    ticketType: typeof ticket
  });
  
  if (!ticket) {
    console.error('❌ onMounted: Ticket not injected!');
    return;
  }
  
  // If ticket data is already available, fetch immediately
  if (ticket?.data) {
    const rawContactName = ticket.data.contact?.name || ticket.data.contact;
    const contactName = truncateContactName(rawContactName);
    if (contactName) {
      console.log('✅ onMounted: Calling fetchOrderHistory - contact found:', contactName);
      setTimeout(() => {
        fetchOrderHistory();
      }, 100);
    } else {
      console.log('⚠️ onMounted: No contact name found in ticket data');
    }
  } else {
    console.log('⏳ onMounted: Ticket data not loaded yet, will fetch when data becomes available', {
      ticketLoading: ticket?.loading,
      ticketData: ticket?.data
    });
  }
});

// Watch for ticketId changes to reset fetch flag
watch(
  () => props.ticketId,
  () => {
    hasFetched.value = false;
  }
);

// Watch for ticket to become available first
watch(
  () => ticket,
  (ticketResource) => {
    console.log('🔔 Watch ticket triggered', { 
      hasTicket: !!ticket,
      hasTicketResource: !!ticketResource,
      ticketResource,
      loading: ticketResource?.loading,
      hasData: !!ticketResource?.data,
      data: ticketResource?.data
    });
    
    // Once ticket is available and data is loaded, watch for data changes
    if (ticketResource && ticketResource.data && !hasFetched.value && !fetching.value) {
      const rawContactName = ticketResource.data.contact?.name || ticketResource.data.contact;
      const contactName = truncateContactName(rawContactName);
      if (contactName) {
        console.log('✅ Watch ticket: Calling fetchOrderHistory - contact found:', contactName);
        setTimeout(() => {
          fetchOrderHistory();
        }, 200);
      } else {
        console.log('⚠️ Watch ticket: No contact name in ticket data:', { contact: ticketResource.data.contact });
      }
    }
  },
  { immediate: true }
);

// Watch for ticket data changes (deep watch)
watch(
  () => {
    if (!ticket) return null;
    return ticket.data;
  },
  (data) => {
    console.log('🔔 Watch ticket.data triggered', { 
      hasTicket: !!ticket,
      hasData: !!data, 
      hasFetched: hasFetched.value, 
      fetching: fetching.value,
      contact: data?.contact,
      contactName: data?.contact?.name || data?.contact,
      ticketLoading: ticket?.loading
    });
    if (data && !hasFetched.value && !fetching.value) {
      const rawContactName = data.contact?.name || data.contact;
      const contactName = truncateContactName(rawContactName);
      if (contactName) {
        console.log('✅ Watch ticket.data: Calling fetchOrderHistory - contact found:', contactName);
        setTimeout(() => {
          fetchOrderHistory();
        }, 200);
      } else {
        console.log('⚠️ Watch ticket.data: No contact name in ticket data:', { contact: data.contact });
      }
    } else if (!data) {
      console.log('⏳ Watch ticket.data: Ticket data not available yet, waiting...');
    }
  },
  { immediate: true, deep: true }
);

// Also watch for contact to become available
watch(
  () => {
    if (!ticket?.data) return null;
    const raw = ticket.data.contact?.name || ticket.data.contact;
    return truncateContactName(raw);
  },
  (contactName) => {
    console.log('🔔 Watch contact name triggered', { 
      contactName, 
      hasFetched: hasFetched.value, 
      fetching: fetching.value,
      hasData: !!ticket?.data,
      hasTicket: !!ticket
    });
    if (contactName && !hasFetched.value && !fetching.value && ticket?.data) {
      console.log('✅ Watch contact name: Calling fetchOrderHistory:', contactName);
      setTimeout(() => {
        fetchOrderHistory();
      }, 200);
    }
  },
  { immediate: true }
);

async function fetchOrderHistory() {
  // Prevent multiple simultaneous fetches
  if (fetching.value) {
    console.log('Already fetching, skipping...');
    return;
  }

  // Check if ticket is injected
  if (!ticket) {
    console.error('Ticket not injected! Cannot fetch order history.');
    return;
  }

  // Wait for ticket data to be available
  if (!ticket?.data) {
    console.log('Waiting for ticket data...', { 
      hasTicket: !!ticket, 
      loading: ticket?.loading 
    });
    return;
  }

  // Contact is an object, not a string - check for contact.name
  const rawContactName = ticket.data.contact?.name || ticket.data.contact;
  const contactName = truncateContactName(rawContactName);
  
  console.log('Fetch function - contact check:', { 
    rawContactName, 
    contactName, 
    contact: ticket.data.contact 
  });
  
  if (!contactName) {
    console.log('No contact on ticket', { contact: ticket.data.contact });
    hasFetched.value = true; // Mark as fetched to prevent retries
    return;
  }

  fetching.value = true;
  hasFetched.value = true; // Mark as fetched immediately to prevent duplicate calls
  console.log('Starting to fetch order history...', { ticketId: props.ticketId, contactName });

  try {
    // Get Contact and find Customer via DynamicLink
    // Use the raw contact name (with duplication) to fetch the Contact document
    const contactDoc = await call('frappe.client.get', {
      doctype: 'Contact',
      name: rawContactName  // Use raw name to fetch Contact doc
    });

    console.log('Contact document:', contactDoc);
    console.log('Contact links:', contactDoc.links);

    let customer_name = null;
    let hd_customer_name = null;

    if (contactDoc.links) {
      for (let link of contactDoc.links) {
        console.log('Checking link:', link);
        if (link.link_doctype === 'Customer') {
          console.log('Found Customer link:', link.link_name);
          const customerDoc = await call('frappe.client.get', {
            doctype: 'Customer',
            name: link.link_name
          });
          customer_name = customerDoc.customer_name;
          console.log('Customer name from doc:', customer_name);

          // Truncate if duplicated format (e.g., "Alan Tom-Alan Tom" -> "Alan Tom")
          if (customer_name && customer_name.includes('-')) {
            const parts = customer_name.split('-');
            if (parts.length === 2 && parts[0].trim() === parts[1].trim()) {
              customer_name = parts[0].trim();
              console.log('Truncated customer name:', customer_name);
            }
          }
          break;
        } else if (link.link_doctype === 'HD Customer') {
          console.log('Found HD Customer link:', link.link_name);
          const hdCustomerDoc = await call('frappe.client.get', {
            doctype: 'HD Customer',
            name: link.link_name
          });
          hd_customer_name = hdCustomerDoc.customer_name;
          console.log('HD Customer name:', hd_customer_name);
        }
      }
    }

    // If no ERPNext Customer found, try to find one by HD Customer name or contact email
    if (!customer_name && hd_customer_name) {
      console.log('Trying to find ERPNext Customer by name:', hd_customer_name);
      // Try to find ERPNext Customer by customer_name (case-insensitive search)
      try {
        const customers = await call('frappe.client.get_list', {
          doctype: 'Customer',
          filters: [['customer_name', 'like', `%${hd_customer_name}%`]],
          fields: ['name', 'customer_name'],
          limit_page_length: 5
        });
        
        if (customers && customers.length > 0) {
          // Try exact match first
          const exactMatch = customers.find(c => 
            c.customer_name.toLowerCase() === hd_customer_name.toLowerCase()
          );
          customer_name = exactMatch ? exactMatch.customer_name : customers[0].customer_name;
          console.log('Found ERPNext Customer by name match:', customer_name);
        }
      } catch (error) {
        console.log('Error searching for Customer:', error);
      }
    }

    // If still no customer, try by contact's primary contact relationship
    if (!customer_name && contactDoc.name) {
      console.log('Trying to find Customer by primary contact:', contactDoc.name);
      try {
        // Search for customers with this contact as primary contact
        const customers = await call('frappe.client.get_list', {
          doctype: 'Customer',
          filters: [['customer_primary_contact', '=', contactDoc.name]],
          fields: ['name', 'customer_name'],
          limit_page_length: 1
        });
        
        if (customers && customers.length > 0) {
          customer_name = customers[0].customer_name;
          console.log('Found ERPNext Customer by primary contact:', customer_name);
        }
      } catch (error) {
        console.log('Error searching for Customer by primary contact:', error);
      }
    }

    if (!customer_name) {
      console.log('No Customer found. Available links:', contactDoc.links?.map(l => `${l.link_doctype}: ${l.link_name}`));
      // Try one more time - search by contact's email or name directly
      if (contactDoc.email_id || contactDoc.first_name || contactDoc.full_name) {
        const searchName = contactDoc.full_name || `${contactDoc.first_name || ''} ${contactDoc.last_name || ''}`.trim() || contactDoc.email_id;
        console.log('Trying final search by contact name/email:', searchName);
        try {
          const customers = await call('frappe.client.get_list', {
            doctype: 'Customer',
            filters: [
              ['customer_name', 'like', `%${searchName}%`]
            ],
            fields: ['name', 'customer_name'],
            limit_page_length: 10
          });
          
          console.log('Customers found by name search:', customers);
          
          if (customers && customers.length > 0) {
            // Try exact match first (case-insensitive)
            const exactMatch = customers.find(c => 
              c.customer_name.toLowerCase().trim() === searchName.toLowerCase().trim()
            );
            // Try partial match (first name or last name)
            const partialMatch = customers.find(c => {
              const cName = c.customer_name.toLowerCase();
              const sName = searchName.toLowerCase();
              const parts = sName.split(' ');
              return parts.some(part => part.length > 2 && cName.includes(part));
            });
            
            customer_name = exactMatch?.customer_name || partialMatch?.customer_name || customers[0].customer_name;
            console.log('Selected Customer:', customer_name);
          }
        } catch (error) {
          console.error('Error in final customer search:', error);
        }
      }
      
      if (!customer_name) {
        console.error('Failed to find Customer. Contact:', contactDoc.name, 'Links:', contactDoc.links);
        const errorMsg = hd_customer_name 
          ? __('No ERPNext Customer found matching HD Customer "%s". Please link the Contact to an ERPNext Customer.', hd_customer_name)
          : __('No Customer linked to this Contact. Please link the Contact to an ERPNext Customer.');
        toast.error(errorMsg);
        fetching.value = false;
        return;
      }
    }

    console.log('Calling API with:', { ticket_name: props.ticketId, customer_name });
    const result = await call('helpdesk.api.order_history.fetch_ticket_order_history', {
      ticket_name: props.ticketId,
      customer_name: customer_name
    });
    
    console.log('API result:', result);

    if (result.success) {
      toast.success(result.message);
      // Reload the ticket document resource to get updated data
      if (ticket?.reload) {
        await ticket.reload();
      }
      // Also manually fetch the updated ticket to ensure reactivity
      const updatedTicket = await call('frappe.client.get', {
        doctype: 'HD Ticket',
        name: props.ticketId,
        fields: ['name', 'custom_order_history']
      });
      // Update the ticket data reactively
      if (ticket?.data && updatedTicket) {
        ticket.data.custom_order_history = updatedTicket.custom_order_history || [];
      }
    } else {
      console.error('API returned error:', result.message);
      toast.error(result.message || __('Failed to fetch order history'));
    }
  } catch (error) {
    console.error('Error fetching order history:', error);
    toast.error(__('Error fetching order history. Check Error Log.'));
  } finally {
    fetching.value = false;
  }
}
</script>

