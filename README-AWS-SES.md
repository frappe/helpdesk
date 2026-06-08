# AWS SES Email Override - Helpdesk App

## Overview

Complete AWS SES email transport implementation for the Helpdesk app, enabling toggleable email delivery through AWS SES or native Frappe Email Account.

**Status**: ✅ Ready for Configuration

## Features

- 🔄 **Toggleable Transport**: Switch between AWS SES and native Email Account with configuration only
- 📧 **Transparent Integration**: Product code continues using `frappe.sendmail`
- 📊 **Email Queue Preservation**: All sends create Email Queue records for visibility
- 🔒 **Privacy-Safe Logging**: Masks recipient emails and never logs AWS secrets
- ⚡ **Size-Based Routing**: Automatic SES v1 (≤10MB) / v2 (>10MB) selection
- 🏥 **Comprehensive Healthcheck**: Validates settings, hooks, credentials, and SES quota
- 🔐 **Security**: Supports explicit credentials or IAM role-based authentication

## Architecture

### Email Flow (SES Enabled)

```
frappe.sendmail(...)
  → Email Queue created
  → SesAwareEmailQueue.send()
    → override_email_send hook
      → helpdesk.email.aws_ses_override.send
        → SES v1 (≤10MB) or SES v2 (>10MB)
```

### Email Flow (SES Disabled)

```
frappe.sendmail(...)
  → Email Queue created
  → Native Frappe Email Account
    → SMTP or Frappe Mail service
```

## Quick Start

### 1. Install Boto3

```bash
# Activate bench environment
cd /home/ubuntu/frappe-bench
source env/bin/activate

# Install boto3
pip install boto3
```

### 2. Migrate DocType

```bash
# Run migration to create AWS SES Settings DocType
bench --site <site-name> migrate
```

### 3. Configure AWS SES Settings

Navigate to: **Desk → Setup → AWS SES Settings**

**Required fields when enabled:**
- ✅ Enable AWS SES (checkbox)
- ✅ AWS Region (e.g., `us-east-1`)
- ✅ Default Sender Email (must be verified in SES)

**Optional fields:**
- Default Sender Name
- Configuration Set Name
- Endpoint URL (for custom endpoints)
- Profile Name (for AWS CLI profiles)
- Retry Mode: `standard` / `adaptive` / `legacy`
- Total Max Attempts: Default `3`

**Explicit Credentials (if not using IAM role):**
- Use Explicit Credentials (checkbox)
- Access Key ID
- Secret Access Key
- Session Token (optional)

### 4. Run Healthcheck

```bash
# Via bench console
bench --site <site-name> console

# Run healthcheck
frappe.call('helpdesk.email.aws_ses_healthcheck.run')
```

Or via Postman/API:
```
POST /api/method/helpdesk.email.aws_ses_healthcheck.run
```

**Expected response when ready:**
```json
{
  "status": "ready",
  "checks": [
    {"name": "SES Enabled", "status": "pass"},
    {"name": "AWS Region", "status": "pass", "value": "us-east-1"},
    {"name": "Default Sender Email", "status": "pass", "value": "s***@e***.com"},
    {"name": "Email Send Hook", "status": "pass"},
    {"name": "AWS Credentials", "status": "pass"},
    {"name": "SES Quota", "status": "pass"}
  ],
  "remediation": []
}
```

### 5. Send Test Email

```bash
# Via bench console
bench --site <site-name> console

# Send test email
frappe.sendmail(
    recipients=["test@example.com"],
    subject="AWS SES Test Email",
    message="<p>This is a test email via AWS SES.</p>",
    now=True
)
```

Check Email Queue:
```
Desk → Email → Email Queue
```

## Configuration Examples

### Example 1: IAM Role-Based (Recommended for EC2/ECS)

```python
# AWS SES Settings
enabled = 1
aws_region = "us-east-1"
default_sender_email = "support@helpdesk.example.com"
default_sender_name = "Helpdesk Support"
use_explicit_credentials = 0  # Use IAM role
```

### Example 2: Explicit Credentials

```python
# AWS SES Settings
enabled = 1
aws_region = "us-west-2"
default_sender_email = "noreply@helpdesk.example.com"
default_sender_name = "Helpdesk"
use_explicit_credentials = 1
access_key_id = "AKIAIOSFODNN7EXAMPLE"
secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

### Example 3: With Configuration Set

```python
# AWS SES Settings
enabled = 1
aws_region = "eu-west-1"
default_sender_email = "support@helpdesk.eu"
configuration_set_name = "helpdesk-tracking"  # For bounce/complaint tracking
```

## Testing

### Unit Tests

```bash
# Test configuration loading
bench --site <site-name> run-tests --app helpdesk --module helpdesk.tests.test_aws_ses_config

# Test schema validation
bench --site <site-name> run-tests --app helpdesk --module helpdesk.tests.test_aws_ses_settings_schema
```

### Integration Test (Manual)

```bash
# 1. Enable SES
# 2. Send test email
# 3. Check Email Queue status
# 4. Verify email delivered to recipient
# 5. Disable SES
# 6. Configure native Email Account
# 7. Send test email via native transport
```

## MFA/OTP Email Support

The AWS SES override **automatically handles** MFA and forgot password emails sent by Frappe's authentication system:

### Forgot Password Flow
```python
# Frappe calls internally (no changes needed):
frappe.sendmail(
    recipients=[user_email],
    subject="Password Reset",
    message="<reset link>",
)
# → Routed through SES when enabled
```

### MFA OTP Flow
```python
# Frappe 2FA calls internally:
frappe.sendmail(
    recipients=[user_email],
    subject="Your OTP",
    message="Your OTP code is: 123456",
)
# → Routed through SES when enabled
```

**No custom OTP template needed** - Frappe's built-in templates work automatically through the override.

## Troubleshooting

### Issue: Healthcheck fails with "Credential error"

**Solution:**
- If using IAM role: Check EC2/ECS instance role has SES permissions
- If using explicit credentials: Verify Access Key ID and Secret Access Key
- Test credentials with AWS CLI:
  ```bash
  aws ses get-send-quota --region us-east-1
  ```

### Issue: "Sender email not verified"

**Solution:**
- Go to AWS SES Console
- Navigate to Verified Identities
- Add and verify your sender email or domain
- For production: Request production access (remove sandbox limits)

### Issue: Native Email Account fails when SES disabled

**Solution:**
- Configure a native outgoing Email Account:
  ```
  Desk → Email → Email Account
  - Enable Outgoing: ✓
  - Default Outgoing: ✓
  - SMTP Server: smtp.gmail.com (example)
  - Port: 587
  - Use TLS: ✓
  ```

### Issue: Hook conflicts

**Solution:**
- Check `hooks.py` for other apps registering `override_email_send`
- Only one app can own the hook
- Run healthcheck to detect conflicts

### Issue: Email Queue status stuck at "Sending"

**Solution:**
- Check error logs:
  ```bash
  tail -f sites/<site-name>/logs/error.log
  ```
- Verify AWS SES quota not exceeded
- Check IAM permissions include `ses:SendRawEmail` and `sesv2:SendEmail`

## Rollback Procedure

### Option 1: Disable SES (Keep Configuration)

1. Open **AWS SES Settings**
2. Uncheck **Enable AWS SES**
3. Save
4. Configure native Email Account
5. Send test email to verify

### Option 2: Remove Hook (Complete Rollback)

```python
# In hooks.py, comment out:
# override_email_send = "helpdesk.email.aws_ses_override.send"

# override_doctype_class = {
#     "Email Queue": "helpdesk.email.email_queue_override.SesAwareEmailQueue",
# }
```

```bash
# Restart services
bench restart
```

## AWS IAM Permissions

### Minimal IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendRawEmail",
        "ses:SendEmail",
        "ses:GetSendQuota",
        "sesv2:SendEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

### Production IAM Policy (with Configuration Set)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendRawEmail",
        "ses:SendEmail",
        "ses:GetSendQuota",
        "sesv2:SendEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:PutConfigurationSetEventDestination",
        "ses:GetConfigurationSet"
      ],
      "Resource": "arn:aws:ses:*:*:configuration-set/helpdesk-tracking"
    }
  ]
}
```

## File Inventory

```
helpdesk/
├── email/
│   ├── __init__.py
│   ├── aws_ses_config.py              # Config loader with caching
│   ├── aws_ses_override.py            # Central transport hook
│   ├── email_queue_override.py        # SES-aware Email Queue
│   ├── ses_email_account_decoupler.py # Synthetic Email Account
│   └── aws_ses_healthcheck.py         # Readiness check
├── helpdesk/
│   └── doctype/
│       └── aws_ses_settings/
│           ├── __init__.py
│           ├── aws_ses_settings.json  # DocType schema
│           └── aws_ses_settings.py    # Controller with validation
├── tests/
│   ├── test_aws_ses_config.py
│   └── test_aws_ses_settings_schema.py
└── hooks.py                            # Hook registration
```

## Support

- **Issues**: https://github.com/frappe/helpdesk/issues
- **Discussions**: https://github.com/frappe/helpdesk/discussions
- **AWS SES Docs**: https://docs.aws.amazon.com/ses/
- **Boto3 SES Docs**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html

## License

AGPLv3 - See LICENSE file for details

---

**Status**: ✅ Implementation Complete  
**Next Step**: Configure AWS SES Settings and run healthcheck

---

*Last updated: 2026-05-25*
