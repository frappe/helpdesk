Tasks Done
- [x] Sync ERPNext customer to HD Customer
- [x] Sync HD Customer to ERPNext customer
- [x] Add Custom field in ERPNext Customer to store HD Customer ID
- [x] Add Field in HD Customer to store ERPNext Customer ID
- [ ] Patch to sync both of the users master
	- [ ] If HD Customer has Customer A,B and ERPNext has Customer A,C then after sync both will have Customer A,B,C. If HD Customer has Customer A,B and ERPNext has Customer C,D then after sync both will have Customer A,B,C,D. If HD Customer has Customer A,B and ERPNext has Customer A,B then after sync both will have Customer A,B.

- [ ] Add a button in Customer.vue in frontend 'Sync with ERPNext' to sync with ERPNext Customer by checking if Integration is enabled or not and if erpnext is installed or not and if both have the same count or not
	Calls an API in integrations.erpnext sync_hd_erpnext_customers which will do same thing as above patch so make a common function that can be used in both

- [ ] Add a button in Customer doctype in ERPNext 'Sync with HD' to sync with HD Customer by checking if Integration is enabled or not and if helpdesk is installed or not and if both have the same count or not via Custom List and all scripts, which will come from Helpdesk side


Tasks Left

- [ ] Settings in HD to toggle integration
- [ ] Desk UI HD Customer hide field
