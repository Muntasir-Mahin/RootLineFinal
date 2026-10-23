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
