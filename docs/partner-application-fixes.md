# Partner application fixes: phase results and file inventory

Baseline: 267 tests, 266 passed; the existing reviews migration test errors on accounts_user.theme_preference.

Read-only legacy audit of the cloud database: 0 matching partner-<32 hex> users and 0 linked companies. Local/production databases are not visible here. No legacy account conversion, rename, merge or deletion is included. Legacy email login is supported through customer login without changing IDs or passwords.

## Flaw 1

Full suite: 273 tests, 272 passed; only the same pre-existing reviews migration error on accounts_user.theme_preference remains. All 43 Partner tests passed, including identity preservation, resubmission, private uploads, verification expiry/replay/email binding, CSRF and legacy login. Migration applied; system/drift checks passed.

| File | Reason |
| --- | --- |
| `accounts/navigation.py` | Validate internal return URLs for login and Terms navigation. |
| `accounts/templates/accounts/login.html` | Remove separate company-login link; preserve next and show customer-signup guidance. |
| `accounts/templates/accounts/profile.html` | Add Partner Dashboard/application-status/apply link to the existing account page. |
| `accounts/templates/accounts/register.html` | Carry a validated partnership return URL through ordinary customer signup. |
| `accounts/views.py` | Preserve validated next URLs; add legacy-only email-login compatibility while retaining the existing default redirect. |
| `docs/partner-application-fixes.md` | Record every changed/created/deleted file, purpose and each phase test result. |
| `partners/admin.py` | Keep customer email separate and route Partner administration through audited services. |
| `partners/application_views.py` | Serve authenticated apply, status, email verification and private license download pages. |
| `partners/auth.py` | Authenticate only legacy partner-UUID accounts by their old company-email credentials. |
| `partners/email_verification.py` | Bind a one-hour, single-use signed link to the customer, current email and nonce; throttle resend. |
| `partners/forms.py` | Replace password-based company registration with customer application and validated optional license upload. |
| `partners/migrations/0007_companyprofile_submitted_at_and_more.py` | New schema migration for the scoped application/notification fields. |
| `partners/models.py` | Add private license/application metadata and separate email-verification records without altering User. |
| `partners/services.py` | Attach/resubmit the same company to the customer; change Partner-group access through approval/suspension. |
| `partners/static/partners/partners.css` | Rebuild only Partner-scoped Tailwind utilities. |
| `partners/templates/partners/account_link.html` | Reuse one conditional Partner link in account/navigation locations. |
| `partners/templates/partners/application_status.html` | Show pending/approved/rejected/suspended status and resubmission/private-license links. |
| `partners/templates/partners/directory.html` | Link to customer application instead of separate company registration. |
| `partners/templates/partners/login.html` | Remove the obsolete separate login template; its URL redirects safely. |
| `partners/templates/partners/register.html` | Render the password-free application and multipart license upload. |
| `partners/templates/partners/verify_email.html` | Request customer-email verification before applying. |
| `partners/templates/partners/verify_email_confirm.html` | Confirm verification with CSRF protection; GET does not verify an address. |
| `partners/tests/test_accounts.py` | Replace obsolete independent-registration expectations with the new access rules. |
| `partners/tests/test_applications.py` | Test identity preservation, eligibility, privacy, resubmission, verification and legacy compatibility. |
| `partners/urls.py` | Add application/verification/private-license routes and retain legacy route names. |
| `partners/views.py` | Redirect obsolete registration/login URLs; gate Partner operations; keep customer email separate. |
| `templates/base.html` | Add the conditional Partner link and/or authenticated notification indicator without changing other navigation. |

## Flaw 2

Full suite: 283 tests, 282 passed; the same pre-existing reviews migration error remains. All 53 Partner tests passed, including role permissions, staff/applicant in-app and email notifications, private document access, idempotent decisions and a concurrent-decision race. Focused Partner/dashboard suite also passed. New migrations applied; system/drift checks passed.

| File | Reason |
| --- | --- |
| `.env.example` | Document fake comma-separated STAFF_NOTIFICATION_EMAILS values. |
| `dashboard/forms.py` | Require a reason for Partner rejection. |
| `dashboard/management/commands/create_dashboard_roles.py` | Include Partners in the existing role setup command description. |
| `dashboard/partner_views.py` | List/filter/review applications using the shared approval service. |
| `dashboard/permissions.py` | Add the Partners role without changing other role checks. |
| `dashboard/templates/dashboard/base.html` | Add Partners queue navigation and notification unread indicator. |
| `dashboard/templates/dashboard/overview.html` | Add the pending Partner applications card. |
| `dashboard/templates/dashboard/partner_detail.html` | Render the new application/notification workflow using existing design classes. |
| `dashboard/templates/dashboard/partners.html` | Render the new application/notification workflow using existing design classes. |
| `dashboard/tests.py` | Extend the exact dashboard queue-count expectation for the new Partners queue. |
| `dashboard/urls.py` | Add staff Partner list/detail/decision routes. |
| `dashboard/views.py` | Expose pending Partner count and role-gated navigation in staff pages. |
| `docs/partner-application-fixes.md` | Record every changed/created/deleted file, purpose and each phase test result. |
| `notifications/__init__.py` | Implement the generic notification service, permissions or delivery workflow. |
| `notifications/admin.py` | Implement the generic notification service, permissions or delivery workflow. |
| `notifications/apps.py` | Implement the generic notification service, permissions or delivery workflow. |
| `notifications/context_processors.py` | Implement the generic notification service, permissions or delivery workflow. |
| `notifications/migrations/0001_initial.py` | New schema migration for the scoped application/notification fields. |
| `notifications/migrations/__init__.py` | New schema migration for the scoped application/notification fields. |
| `notifications/models.py` | Implement the generic notification service, permissions or delivery workflow. |
| `notifications/services.py` | Implement the generic notification service, permissions or delivery workflow. |
| `notifications/templates/notifications/bell.html` | Render the new application/notification workflow using existing design classes. |
| `notifications/templates/notifications/inbox.html` | Render the new application/notification workflow using existing design classes. |
| `notifications/urls.py` | Implement the generic notification service, permissions or delivery workflow. |
| `notifications/views.py` | Implement the generic notification service, permissions or delivery workflow. |
| `partners/admin.py` | Keep customer email separate and route Partner administration through audited services. |
| `partners/application_notifications.py` | Notify eligible staff and applicant in-app/by email after committed actions. |
| `partners/application_views.py` | Serve authenticated apply, status, email verification and private license download pages. |
| `partners/migrations/0008_companyprofile_decided_at_companyprofile_decided_by_and_more.py` | New schema migration for the scoped application/notification fields. |
| `partners/models.py` | Add private license/application metadata and separate email-verification records without altering User. |
| `partners/services.py` | Attach/resubmit the same company to the customer; change Partner-group access through approval/suspension. |
| `partners/templates/partners/application_status.html` | Show pending/approved/rejected/suspended status and resubmission/private-license links. |
| `partners/tests/test_accounts.py` | Replace obsolete independent-registration expectations with the new access rules. |
| `partners/tests/test_concurrency.py` | Add scoped regression coverage for this phase. |
| `partners/tests/test_staff_applications.py` | Add scoped regression coverage for this phase. |
| `rootline/settings.py` | Register generic notifications and unread-count context; load staff notification recipients from environment. |
| `rootline/urls.py` | Include the generic notifications URL namespace. |
| `templates/base.html` | Add the conditional Partner link and/or authenticated notification indicator without changing other navigation. |
