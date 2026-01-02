# i18n Translation Plan for Vue Components

## Overview

This document tracks the progress of adding translation wrappers `__()` to all Vue components in the Frappe Helpdesk frontend.

**Branch:** `feat/i18n-vue-translations`
**Related PR:** https://github.com/frappe/helpdesk/pull/2836
**Started:** 2026-01-01

## Translation Pattern

```typescript
// Import the translation function
import { __ } from "@/translation";

// In template - wrap user-facing strings
{{ __("Submit") }}

// With interpolation
{{ __("{0} tickets found", [count]) }}

// In script - same pattern
const title = __("Settings");
```

## Statistics

- **Total Vue files:** 271
- **Files with translations:** 57
- **Files needing translation (excluding icons):** ~172
- **Icon components (no translation needed):** 42

---

## Progress Tracker

### Legend
- [ ] Not started
- [x] Completed
- [~] In progress

---

## Priority 1: Settings Components (High Impact)

### Settings/Assignment Rules/
- [ ] `desk/src/components/Settings/Assignment Rules/AssigneeRules.vue`
- [x] `desk/src/components/Settings/Assignment Rules/AssigneeSearch.vue`
- [x] `desk/src/components/Settings/Assignment Rules/AssignmentRuleListItem.vue`
- [x] `desk/src/components/Settings/Assignment Rules/AssignmentRuleView.vue`
- [ ] `desk/src/components/Settings/Assignment Rules/AssignmentRules.vue`
- [ ] `desk/src/components/Settings/Assignment Rules/AssignmentRulesList.vue`
- [ ] `desk/src/components/Settings/Assignment Rules/AssignmentRulesListView.vue`
- [x] `desk/src/components/Settings/Assignment Rules/AssignmentRulesSection.vue`
- [x] `desk/src/components/Settings/Assignment Rules/AssignmentSchedule.vue`
- [ ] `desk/src/components/Settings/Assignment Rules/AssignmentScheduleItem.vue`

### Settings/EmailNotifications/
- [ ] `desk/src/components/Settings/EmailNotifications/Acknowledgement.vue`
- [ ] `desk/src/components/Settings/EmailNotifications/EmailNotifications.vue`
- [ ] `desk/src/components/Settings/EmailNotifications/Notification.vue`
- [x] `desk/src/components/Settings/EmailNotifications/NotificationList.vue`
- [ ] `desk/src/components/Settings/EmailNotifications/ReplyToAgents.vue`
- [ ] `desk/src/components/Settings/EmailNotifications/ReplyViaAgent.vue`
- [x] `desk/src/components/Settings/EmailNotifications/ShareFeedback.vue`

### Settings/FieldDependency/
- [x] `desk/src/components/Settings/FieldDependency/FieldDependency.vue`
- [ ] `desk/src/components/Settings/FieldDependency/FieldDependencyConfig.vue`
- [ ] `desk/src/components/Settings/FieldDependency/FieldDependencyCriteria.vue`
- [ ] `desk/src/components/Settings/FieldDependency/FieldDependencyFieldsSelection.vue`
- [x] `desk/src/components/Settings/FieldDependency/FieldDependencyList.vue`
- [ ] `desk/src/components/Settings/FieldDependency/FieldDependencyValueSelection.vue`

### Settings/General/
- [x] `desk/src/components/Settings/General/General.vue`
- [x] `desk/src/components/Settings/General/components/Branding.vue`
- [ ] `desk/src/components/Settings/General/components/LogoUpload.vue`
- [ ] `desk/src/components/Settings/General/components/TicketSettings.vue`
- [ ] `desk/src/components/Settings/General/components/WorkflowKnowledgebaseSettings.vue`

### Settings/Holiday/
- [ ] `desk/src/components/Settings/Holiday/HLCalender.vue`
- [ ] `desk/src/components/Settings/Holiday/Holiday.vue`
- [ ] `desk/src/components/Settings/Holiday/HolidayList.vue`
- [x] `desk/src/components/Settings/Holiday/HolidayListItem.vue`
- [x] `desk/src/components/Settings/Holiday/HolidayView.vue`
- [ ] `desk/src/components/Settings/Holiday/Holidays.vue`
- [ ] `desk/src/components/Settings/Holiday/HolidaysCalendarView.vue`
- [ ] `desk/src/components/Settings/Holiday/HolidaysTableView.vue`
- [ ] `desk/src/components/Settings/Holiday/Modals/AddHolidayModal.vue`
- [ ] `desk/src/components/Settings/Holiday/RecurringHolidaysList.vue`

### Settings/Profile/
- [x] `desk/src/components/Settings/Profile/Profile.vue`
- [x] `desk/src/components/Settings/Profile/components/ChangePasswordModal.vue`

### Settings/SavedReplies/
- [ ] `desk/src/components/Settings/SavedReplies/SavedReplies.vue`
- [x] `desk/src/components/Settings/SavedReplies/SavedRepliesList.vue`
- [x] `desk/src/components/Settings/SavedReplies/SavedReplyView.vue`
- [ ] `desk/src/components/Settings/SavedReplies/components/FieldAutocompleteList.vue`
- [x] `desk/src/components/Settings/SavedReplies/components/PreviewDialog.vue`

### Settings/Sla/
- [ ] `desk/src/components/Settings/Sla/Sla.vue`
- [ ] `desk/src/components/Settings/Sla/SlaAssignmentConditions.vue`
- [ ] `desk/src/components/Settings/Sla/SlaHolidays.vue`
- [ ] `desk/src/components/Settings/Sla/SlaPolicies.vue`
- [ ] `desk/src/components/Settings/Sla/SlaPolicyList.vue`
- [x] `desk/src/components/Settings/Sla/SlaPolicyListItem.vue`
- [x] `desk/src/components/Settings/Sla/SlaPolicyView.vue`
- [ ] `desk/src/components/Settings/Sla/SlaPriorityList.vue`
- [ ] `desk/src/components/Settings/Sla/SlaPriorityListItem.vue`
- [ ] `desk/src/components/Settings/Sla/SlaStatusList.vue`
- [ ] `desk/src/components/Settings/Sla/SlaWorkDaysList.vue`
- [ ] `desk/src/components/Settings/Sla/SlaWorkDaysListItem.vue`
- [ ] `desk/src/components/Settings/Sla/Modals/EditResponseResolutionModal.vue`
- [ ] `desk/src/components/Settings/Sla/Modals/WorkDayModal.vue`

### Settings/Teams/
- [ ] `desk/src/components/Settings/Teams/NewTeam.vue` (has import but may need more strings)
- [x] `desk/src/components/Settings/Teams/RenameTeamModal.vue`
- [x] `desk/src/components/Settings/Teams/TeamEdit.vue`
- [ ] `desk/src/components/Settings/Teams/TeamsConfig.vue`
- [x] `desk/src/components/Settings/Teams/TeamsList.vue`
- [ ] `desk/src/components/Settings/Teams/components/AgentSelector.vue`

### Settings/Telephony/
- [x] `desk/src/components/Settings/Telephony/Telephony.vue`

### Settings/ (root level)
- [ ] `desk/src/components/Settings/AgentCard.vue`
- [ ] `desk/src/components/Settings/Agents.vue`
- [x] `desk/src/components/Settings/EmailAccountCard.vue`
- [ ] `desk/src/components/Settings/EmailAccountList.vue`
- [x] `desk/src/components/Settings/EmailAdd.vue`
- [ ] `desk/src/components/Settings/EmailConfig.vue`
- [x] `desk/src/components/Settings/EmailEdit.vue`
- [ ] `desk/src/components/Settings/EmailProviderIcon.vue`
- [x] `desk/src/components/Settings/InviteAgents.vue`
- [x] `desk/src/components/Settings/NewTeamModal.vue`
- [ ] `desk/src/components/Settings/SettingsLayoutHeader.vue`
- [ ] `desk/src/components/Settings/SettingsModal.vue`

---

## Priority 2: Modal and Core Components

### Modals
- [x] `desk/src/components/modals/ShortcutsModal.vue`
- [ ] `desk/src/components/ViewModal.vue`
- [ ] `desk/src/components/ConfirmDialog.vue`
- [x] `desk/src/components/ticket/ExportModal.vue`
- [x] `desk/src/components/ticket/SetContactPhoneModal.vue`
- [ ] `desk/src/components/ticket/TicketMergeModal.vue`
- [ ] `desk/src/components/ticket/TicketSplitModal.vue`
- [ ] `desk/src/components/knowledge-base/CategoryModal.vue`
- [ ] `desk/src/components/knowledge-base/MergeCategoryModal.vue`
- [ ] `desk/src/components/knowledge-base/MoveToCategoryModal.vue`
- [ ] `desk/src/components/AssignmentModal.vue`
- [x] `desk/src/components/SavedRepliesSelectorModal.vue`

### Core Components
- [ ] `desk/src/components/Apps.vue`
- [ ] `desk/src/components/AttachmentItem.vue`
- [ ] `desk/src/components/Autocomplete.vue`
- [ ] `desk/src/components/BrandLogo.vue`
- [ ] `desk/src/components/CallArea.vue`
- [ ] `desk/src/components/CommentBox.vue`
- [ ] `desk/src/components/CommentTextEditor.vue`
- [ ] `desk/src/components/CommunicationArea.vue`
- [ ] `desk/src/components/CustomActions.vue`
- [ ] `desk/src/components/DiscardButton.vue`
- [ ] `desk/src/components/DocumentationButton.vue`
- [ ] `desk/src/components/EmailArea.vue`
- [ ] `desk/src/components/EmailContent.vue`
- [ ] `desk/src/components/EmailEditor.vue`
- [ ] `desk/src/components/EmptyState.vue`
- [ ] `desk/src/components/FadedScrollableDiv.vue`
- [ ] `desk/src/components/HistoryBox.vue`
- [ ] `desk/src/components/Icon.vue`
- [ ] `desk/src/components/IconPicker.vue`
- [ ] `desk/src/components/LayoutHeader.vue`
- [ ] `desk/src/components/ListRows.vue`
- [x] `desk/src/components/ListViewBuilder.vue`
- [ ] `desk/src/components/MultiSelect.vue`
- [ ] `desk/src/components/MultiSelectInput.vue`
- [ ] `desk/src/components/MultipleAvatar.vue`
- [ ] `desk/src/components/NestedPopover.vue`
- [ ] `desk/src/components/PageTitle.vue`
- [ ] `desk/src/components/Password.vue`
- [ ] `desk/src/components/Pill.vue`
- [ ] `desk/src/components/Resizer.vue`
- [ ] `desk/src/components/SearchArticles.vue`
- [ ] `desk/src/components/SearchComplete.vue`
- [ ] `desk/src/components/SearchMultiSelect.vue`
- [ ] `desk/src/components/SearchPopover.vue`
- [ ] `desk/src/components/Section.vue`
- [ ] `desk/src/components/SelectDropdown.vue`
- [ ] `desk/src/components/SidebarLink.vue`
- [ ] `desk/src/components/StarRating.vue`
- [ ] `desk/src/components/TextEditor.vue`
- [ ] `desk/src/components/TicketField.vue`
- [ ] `desk/src/components/TypingIndicator.vue`
- [ ] `desk/src/components/UniInput.vue`
- [ ] `desk/src/components/UserAvatar.vue`
- [ ] `desk/src/components/UserMenu.vue`
- [ ] `desk/src/components/ViewBreadcrumbs.vue`

---

## Priority 3: Page Components

### Pages/ticket/
- [ ] `desk/src/pages/ticket/MobileTicketAgent.vue` (has import but may need more)
- [ ] `desk/src/pages/ticket/TicketAgent.vue`
- [ ] `desk/src/pages/ticket/TicketBreadcrumbs.vue`
- [ ] `desk/src/pages/ticket/TicketCommunication.vue`
- [ ] `desk/src/pages/ticket/TicketConversation.vue`
- [x] `desk/src/pages/ticket/TicketCustomer.vue`
- [ ] `desk/src/pages/ticket/TicketCustomerTemplateFields.vue`
- [x] `desk/src/pages/ticket/TicketFeedback.vue`
- [x] `desk/src/pages/ticket/TicketNew.vue`
- [ ] `desk/src/pages/ticket/TicketTextEditor.vue`
- [x] `desk/src/pages/ticket/Tickets.vue`

### Pages/knowledge-base/
- [x] `desk/src/pages/knowledge-base/Article.vue`
- [ ] `desk/src/pages/knowledge-base/Articles.vue`
- [x] `desk/src/pages/knowledge-base/KnowledgeBaseAgent.vue`
- [ ] `desk/src/pages/knowledge-base/KnowledgeBaseCustomer.vue`
- [x] `desk/src/pages/knowledge-base/NewArticle.vue`

### Pages/dashboard/
- [x] `desk/src/pages/dashboard/Dashboard.vue`

### Pages/desk/
- [ ] `desk/src/pages/desk/AgentRoot.vue`
- [x] `desk/src/pages/desk/contact/ContactDialog.vue`
- [ ] `desk/src/pages/desk/contact/Contacts.vue`
- [ ] `desk/src/pages/desk/customer/CustomerDialog.vue`
- [ ] `desk/src/pages/desk/customer/Customers.vue`

### Pages/call-logs/
- [ ] `desk/src/pages/call-logs/CallLogDetailModal.vue`
- [x] `desk/src/pages/call-logs/CallLogModal.vue`
- [ ] `desk/src/pages/call-logs/CallLogs.vue`

### Pages/ (root level)
- [ ] `desk/src/pages/CustomerPortalRoot.vue`
- [ ] `desk/src/pages/HRoot.vue`
- [ ] `desk/src/pages/InvalidPage.vue`
- [x] `desk/src/pages/MobileNotifications.vue`
- [x] `desk/src/pages/SearchAgent.vue`

---

## Priority 4: Layout and Utility Components

### Layouts
- [ ] `desk/src/components/layouts/AppHeader.vue`
- [ ] `desk/src/components/layouts/DesktopLayout.vue`
- [ ] `desk/src/components/layouts/MobileAppHeader.vue`
- [ ] `desk/src/components/layouts/MobileLayout.vue`
- [ ] `desk/src/components/layouts/MobileSidebar.vue`
- [ ] `desk/src/components/layouts/SettingsLayoutBase.vue`
- [x] `desk/src/components/layouts/Sidebar.vue`

### Ticket Agent Components
- [ ] `desk/src/components/ticket-agent/AssignTo.vue`
- [ ] `desk/src/components/ticket-agent/AssignToBody.vue`
- [ ] `desk/src/components/ticket-agent/FeedbackBox.vue`
- [ ] `desk/src/components/ticket-agent/TicketActivityPanel.vue`
- [ ] `desk/src/components/ticket-agent/TicketContact.vue`
- [ ] `desk/src/components/ticket-agent/TicketContactTab.vue`
- [ ] `desk/src/components/ticket-agent/TicketDetailsTab.vue`
- [x] `desk/src/components/ticket-agent/TicketHeader.vue`
- [ ] `desk/src/components/ticket-agent/TicketNavigation.vue`
- [ ] `desk/src/components/ticket-agent/TicketSLA.vue`
- [ ] `desk/src/components/ticket-agent/TicketSidebar.vue`
- [ ] `desk/src/components/ticket-agent/TicketSubjectModal.vue`

### Ticket Components
- [x] `desk/src/components/ticket/ActivityHeader.vue`
- [ ] `desk/src/components/ticket/TicketAgentActivities.vue`
- [ ] `desk/src/components/ticket/TicketAgentContact.vue`
- [ ] `desk/src/components/ticket/TicketAgentDetails.vue`
- [ ] `desk/src/components/ticket/TicketAgentFields.vue`
- [x] `desk/src/components/ticket/TicketAgentSidebar.vue`
- [ ] `desk/src/components/ticket/TicketCustomerSidebar.vue`
- [ ] `desk/src/components/ticket/TicketFeedback.vue`

### Knowledge Base Components
- [ ] `desk/src/components/knowledge-base/ArticleCard.vue`
- [ ] `desk/src/components/knowledge-base/ArticleFeedback.vue`
- [ ] `desk/src/components/knowledge-base/CategoryFolder.vue`
- [ ] `desk/src/components/knowledge-base/CategoryFolderContainer.vue`

### View Controls
- [ ] `desk/src/components/view-controls/ColumnSettings.vue`
- [ ] `desk/src/components/view-controls/Filter.vue`
- [ ] `desk/src/components/view-controls/QuickFilterField.vue`
- [ ] `desk/src/components/view-controls/QuickFilters.vue`
- [ ] `desk/src/components/view-controls/Reload.vue`
- [ ] `desk/src/components/view-controls/SortBy.vue`

### Command Palette
- [x] `desk/src/components/command-palette/CP.vue`
- [ ] `desk/src/components/command-palette/CPGroup.vue`
- [ ] `desk/src/components/command-palette/CPGroupResult.vue`

### Conditions Filter
- [ ] `desk/src/components/conditions-filter/CFCondition.vue`
- [ ] `desk/src/components/conditions-filter/CFConditions.vue`

### Desk Global
- [ ] `desk/src/components/desk/global/AddNewAgentsDialog.vue`
- [ ] `desk/src/components/desk/global/CustomIcons.vue`
- [x] `desk/src/components/desk/global/NewContactDialog.vue`
- [ ] `desk/src/components/desk/global/NewCustomerDialog.vue`

### Frappe UI Wrappers
- [ ] `desk/src/components/frappe-ui/Autocomplete.vue`
- [ ] `desk/src/components/frappe-ui/Dropdown.vue`
- [ ] `desk/src/components/frappe-ui/DurationField.vue`
- [ ] `desk/src/components/frappe-ui/DurationPicker.vue`
- [ ] `desk/src/components/frappe-ui/Link.vue`
- [ ] `desk/src/components/frappe-ui/MultiSelectCombobox.vue`

### Notifications
- [ ] `desk/src/components/notifications/Notifications.vue`

### Telephony
- [ ] `desk/src/components/telephony/CallUI.vue`
- [ ] `desk/src/components/telephony/CountUpTimer.vue`
- [ ] `desk/src/components/telephony/ExotelCallUI.vue`
- [ ] `desk/src/components/telephony/TwilioCallUI.vue`
- [ ] `desk/src/components/telephony/Icons/AvatarIcon.vue`
- [ ] `desk/src/components/telephony/Icons/MinimizeIcon.vue`

### Root Components
- [ ] `desk/src/App.vue`
- [ ] `desk/src/assets/logos/HDLogo.vue`

---

## Excluded Files (No Translation Needed)

### Icon Components (42 files)
All files in `desk/src/components/icons/` are SVG icon components without user-facing text.

---

## Current Progress

**Last Updated:** 2026-01-01

| Category | Total | Completed | Remaining |
|----------|-------|-----------|-----------|
| Settings | 67 | 25 | 42 |
| Modals | 12 | 5 | 7 |
| Core | 44 | 1 | 43 |
| Pages | 27 | 13 | 14 |
| Layouts | 7 | 1 | 6 |
| Ticket Agent | 12 | 1 | 11 |
| Ticket | 8 | 2 | 6 |
| Knowledge Base | 4 | 0 | 4 |
| View Controls | 6 | 0 | 6 |
| Other | 22 | 1 | 21 |
| **TOTAL** | **209** | **49** | **160** |

---

## Session Log

### Session 1 - 2026-01-01
- Created branch `feat/i18n-vue-translations` from upstream/develop
- Created this translation plan document
- Completed Settings/Assignment Rules/ translations
- Completed Settings/EmailNotifications/ translations
- Completed Settings/FieldDependency/ translations
- Completed Settings/Holiday/ translations

**Files Modified:**
1. `AssigneeRules.vue` - Added import and translated ticketRoutingOptions labels
2. `Notification.vue` - Added import (already using __ in template)
3. `FieldDependencyCriteria.vue` - Full translation
4. `FieldDependencyFieldsSelection.vue` - Translated Parent/Child Field labels
5. `FieldDependencyValueSelection.vue` - Full translation
6. `HLCalender.vue` - Translated Edit/Delete/Recurring holiday
7. `HolidayList.vue` - Added import
8. `Holidays.vue` - Added import
9. `HolidaysTableView.vue` - Full translation
10. `AddHolidayModal.vue` - Full translation
11. `RecurringHolidaysList.vue` - Full translation (days, repetition, labels)

**Currently Working On:** Settings/Sla/
