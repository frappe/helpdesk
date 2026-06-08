# Canned Responses Feature

## Overview

The Canned Responses feature allows support agents to create, manage, and quickly insert pre-written responses into ticket comments. This helps improve response time and maintain consistency across support interactions.

## Features

### 1. **Canned Response Management**
   - Create and edit canned responses with rich text formatting
   - Organize responses by category (Greeting, Closing, Troubleshooting, Billing, Account, General, Escalation, Follow-up)
   - Assign shortcuts for quick access (e.g., `/thanks`, `/resolved`)
   - Track usage statistics (count and last used date)
   - Activate/deactivate responses as needed

### 2. **Quick Insert via UI**
   - Click the message icon in the comment editor toolbar
   - Browse and search canned responses
   - Filter by category
   - Preview responses before inserting
   - One-click insertion into comment

### 3. **Keyboard Shortcuts**
   - Type shortcuts directly in the comment box (e.g., `/thanks`)
   - Automatic replacement with the full response
   - Shortcuts are case-insensitive and automatically prefixed with `/`

### 4. **Usage Analytics**
   - Automatic tracking of how often each response is used
   - Last used timestamp for each response
   - Helps identify most valuable responses

## How to Use

### For Agents

#### Using the UI Selector:
1. Open a ticket
2. Click the message icon (💬) in the comment editor toolbar
3. Search or browse for the response you need
4. Click on a response to insert it into your comment
5. Edit as needed and send

#### Using Keyboard Shortcuts:
1. Open a ticket
2. In the comment box, type the shortcut (e.g., `/thanks`)
3. The full response will automatically replace the shortcut
4. Edit as needed and send

### For Administrators

#### Creating Canned Responses:
1. Navigate to `/canned-responses` in the helpdesk app
2. Click "New Response"
3. Fill in:
   - **Title**: A descriptive name for the response
   - **Shortcut**: Optional keyboard shortcut (e.g., `/thanks`)
   - **Category**: Select appropriate category
   - **Message**: The response content (supports rich text)
   - **Is Active**: Check to make it available to agents
4. Save the response

#### Managing Responses:
- View all responses at `/canned-responses`
- Search and filter responses
- Edit existing responses
- Delete unused responses
- Monitor usage statistics

## Pre-loaded Responses

The system comes with 13 default canned responses:

| Shortcut | Title | Category |
|----------|-------|----------|
| `/thanks` | Thank You for Contacting Us | Greeting |
| `/resolved` | Issue Resolved | Closing |
| `/moreinfo` | Request Additional Information | Follow-up |
| `/cache` | Clear Cache and Cookies | Troubleshooting |
| `/internet` | Check Your Internet Connection | Troubleshooting |
| `/password` | Password Reset Instructions | Account |
| `/escalate` | Escalating to Technical Team | Escalation |
| `/billing` | Billing Inquiry - Processing | Billing |
| `/working` | Working on Your Request | General |
| `/followup` | Follow Up Reminder | Follow-up |
| `/verify` | Account Verification Required | Account |
| `/browser` | Browser Compatibility | Troubleshooting |
| `/close` | Ticket Closing | Closing |

## Technical Implementation

### DocType: HD Canned Response

**Fields:**
- `title` (Data): Display name of the response
- `shortcut` (Data): Keyboard shortcut (auto-prefixed with `/`)
- `category` (Select): Response category
- `is_active` (Check): Whether the response is available
- `message` (Text Editor): The response content
- `usage_count` (Int): Number of times used
- `last_used` (Datetime): When it was last used

### API Endpoints

**Get all canned responses:**
```python
helpdesk.helpdesk.doctype.hd_canned_response.hd_canned_response.get_canned_responses(
    search_term=None,
    category=None
)
```

**Use a canned response:**
```python
helpdesk.helpdesk.doctype.hd_canned_response.hd_canned_response.use_canned_response(
    name
)
```

**Get response by shortcut:**
```python
helpdesk.helpdesk.doctype.hd_canned_response.hd_canned_response.get_canned_response_by_shortcut(
    shortcut
)
```

### UI Components

- **CannedResponseSelector.vue**: Popup selector component
- **CommentTextEditor.vue**: Enhanced with canned response integration
- **CannedResponses.vue**: Management page

## Best Practices

1. **Keep responses concise** - Agents can always add more details
2. **Use clear shortcuts** - Make them memorable (e.g., `/thanks` not `/ty`)
3. **Review usage stats** - Identify and improve frequently used responses
4. **Update regularly** - Keep responses current with policies and procedures
5. **Categorize properly** - Makes searching easier for agents
6. **Include placeholders** - Use `[PLACEHOLDER]` where customization is needed

## Future Enhancements

Potential improvements:
- Template variables (e.g., `{{customer_name}}`, `{{ticket_id}}`)
- Multi-language support
- Team-specific responses
- Response suggestions based on ticket content
- Bulk import/export of responses
- Response versioning and history

## Troubleshooting

**Shortcut not working:**
- Ensure the response is marked as "Active"
- Verify the shortcut starts with `/`
- Check for duplicate shortcuts

**Response not appearing in selector:**
- Confirm the response is active
- Check category filters
- Refresh the page

**Installation:**
If sample responses are not loaded:
```bash
bench --site [site_name] execute helpdesk.setup.install_canned_responses.install_canned_responses
```

## Support

For issues or feature requests, please create an issue in the helpdesk repository.
