# Customer → Agro Partner: setup and testing

Customers now apply for partnership from their existing signed-in account. The form never asks for a password or creates a User. Approval adds **Partner Company** membership to that same account; normal shopping and any existing seller access remain available. Pending/rejected applicants use the application-status page. Rejected applicants edit/resubmit the same CompanyProfile. Staff/superuser accounts cannot apply.

This guide replaces the older separate-company registration/login instructions. Partner products, direct buyer/company payments, ledger accounting, billing calculations and verified-purchase review rules are unchanged. Complete per-step file inventories and test results are in [partner-application-fixes.md](partner-application-fixes.md).

## 1. Install and migrate

Back up your existing `.env`, `db.sqlite3`, `media/` and `private_partner_files/`. A fresh GitHub ZIP does not include these ignored files. Keep your working Gmail credentials and stable `DJANGO_SECRET_KEY`.

Open the directory containing `manage.py`, activate your existing virtual environment and run:

```bash
# macOS/Linux
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py create_dashboard_roles
python manage.py check
```

Windows PowerShell activation is `.venv\Scripts\Activate.ps1`; the remaining commands are the same. If this is a fresh checkout without an environment, create one first with `python3 -m venv .venv` (Windows: `py -m venv .venv`). No new package is required.

The new migrations add application/license/decision fields, a separate customer-email verification table, and the generic notifications table. `accounts.User` is unchanged. The existing OneToOne company/user constraint remains. No account merge, rename, password change, deletion or conversion is included.

## 2. Configure staff notification email

In the `.env` file **beside `manage.py`**, add this new variable, replacing the fake recipient addresses:

```dotenv
STAFF_NOTIFICATION_EMAILS=owner@example.com,partner-reviewer@example.com
```

These are additional recipients; active staff in **Partners** and active staff superusers are also notified. Recipients are deduplicated ignoring case. The additional addresses receive email only; they do not gain staff permissions or an in-app account.

Keep your existing `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and `DEFAULT_FROM_EMAIL`. To test without delivering mail:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Console emails print in the `runserver` terminal. They are not delivered to an inbox. For your already configured Gmail sender, switch back to:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

Restart Django after editing `.env`. Empty SMTP credentials produce a warning and skip email; delivery exceptions are logged and do not undo the application/decision. In-app notifications remain available. Staff are notified after submit/resubmit; applicants are notified after approval/rejection, including the staff reason. Decision email goes to the customer account email, rather than changing it to the business contact address.

Email verification requires access to a real message or the console link. If the backend fails, staff can still receive applications already submitted, but a new applicant cannot bypass email verification.

## 3. Create a staff reviewer and assign the Partners role

If you do not have an owner account, run:

```bash
python manage.py createsuperuser
```

Sign in as the owner at `/admin/`. Under **Accounts → Users**, create or edit an ordinary staff reviewer:

1. Give the user a username, password and notification email.
2. Enable **Active** and **Staff status**.
3. In **Groups**, add **Partners**. The `create_dashboard_roles` command creates it if necessary.
4. Save. The reviewer signs in through ordinary `/login/`, then opens `/dashboard/partners/`.

**Partners** is the staff-review role. **Partner Company** is the approved customer's company-access group; approval assigns it automatically. Do not confuse the two. No superuser status or Django model permissions are needed for a reviewer. The existing Django admin remains owner-only.

Partners staff can approve/reject applications. They cannot mark a company verified, suspend/unsuspend it, adjust Partner ledger entries, change Partner billing plans or verify Partner invoice payments. Those operations remain owner-only. Existing Finance/Support/Catalogue permissions are unchanged.

## 4. Apply as an existing customer

1. Visit `/partners/apply/`, or choose **Become an Agro Partner** from your customer account menu/profile or Agro Partners directory.
2. If signed out, Django redirects to customer login with a validated internal `next` URL. The login page says **Create a customer account first, then apply for partnership** and links to customer signup. After signup, sign in normally to continue. The usual login destination remains `/profile/` when no valid `next` is supplied.
3. Verify the email on the customer account. If no email is present, use **Edit customer email** first. Choose **Send verification email**, open the link, sign in to the same customer account if needed, and press **Verify my email**. Merely opening the link does not verify it.
4. The signed link expires after one hour, is bound to that account/current email, and can be used once. A newly sent link invalidates the previous one. Wait one minute between resend requests. Changing the customer email requires verification again before applying/resubmitting; it does not interrupt normal shopping.
5. Enter company name, business contact email, phone, address, district/division, optional trade license number and optional document. The business email is separate from the customer email. A duplicate company name is reported explicitly; other conflicting details get a generic error without identifying another account.
6. Optional trade-license uploads use the existing file validator: PDF/JPG/PNG/WebP, at most 5 MB; images are re-encoded. Files are stored under `private_partner_files/trade-licenses/`, not public media. Only the applicant, Partners staff and owner may download them through the authenticated route. Do not expose this directory through your web server; keep it backed up with the other private files.
7. Read Partner Terms from the link beside the required checkbox. It opens a new tab with a visible hint. The original form remains in its original tab. The Terms page has a Back link that accepts internal paths only.
8. Tick agreement and submit. The same customer account now has a **Pending** application; it has no Partner dashboard access yet. A second submission cannot create another profile. View status through `/partners/application/`.

Company name, district and division are saved in this browser tab's `sessionStorage`, scoped to the signed-in account. They are restored if the application is reopened in that same tab. Passwords, email/phone/address, license details, files, CSRF tokens and agreement are not stored. Failed server validation re-renders the entered text/checkbox values; files must be selected again. A fresh form leaves agreement unchecked. Only a successful server submission clears the saved draft. A new tab has its own session storage; the original form is the one to continue using after reading Terms.

## 5. Review, approve or reject

As Partners staff, open **Staff dashboard → Partners**. The pending badge counts applications; the queue defaults to pending, oldest first. Search by company name or filter pending/approved/rejected/all. Open **Review application** to inspect the fields, customer account, dates and private document.

Choose **Approve** or **Reject**. Rejection requires a nonblank reason. A transaction locks the application, saves the reviewer/time/reason, writes PartnerAuditLog and notifies the applicant. Concurrent/repeated decisions cannot create a second decision or notification. The Django admin actions use the same service.

On approval, the customer's profile/menu shows **Partner Dashboard**. On rejection, the status page shows the staff reason and **Edit and resubmit application**. Resubmission returns the same profile to pending, clears its current decision metadata and retains earlier audit events. Owner suspension removes Partner-group access while retaining the customer's account. Do not deactivate the customer just to suspend their Partner privileges.

Use the bell in customer/staff navigation to open `/notifications/`. Notifications belong only to their recipient. **Mark read** uses a CSRF-protected POST and updates the unread count on the next render; there is no background polling. The generic `notifications.services.create_notification(recipient, message, link)` helper can be reused by other apps later.

## 6. Legacy accounts and old URLs

The cloud database audit found **0 users** matching `partner-<32 hexadecimal characters>` and **0 linked companies** before these changes. Your local/production database was not available for that count. To count there without changing anything:

```bash
python manage.py shell -c "from django.contrib.auth import get_user_model; from partners.models import CompanyProfile; pattern=r'^partner-[0-9a-f]{32}$'; print('Legacy users:', get_user_model().objects.filter(username__regex=pattern).count()); print('Legacy companies:', CompanyProfile.objects.filter(user__username__regex=pattern).count())"
```

Legacy accounts keep their IDs, passwords, profile links, products, orders and invoices. Ordinary customer login additionally accepts the old company-email credentials **only for those legacy partner-UUID users**; ordinary customers still log in by username. Existing approved legacy partners do not have to complete application email verification to keep their current approved dashboard access. No automated migration into a different customer account is provided; any merge/conversion needs a separate reviewed plan and your explicit approval.

`/partners/register/` redirects to the new application flow. `/partners/login/` redirects to ordinary customer login/status. The separate company-login page/link is removed. Neither old URL returns 404.

## 7. Manual end-to-end checklist

1. Start `python manage.py runserver`; use separate browser profiles for customer, reviewer and owner.
2. While signed out, open Apply. Verify the login redirect, signup guidance and safe return after customer signup/login. Try an external `next` URL: it must not redirect off-site.
3. Request email verification with the console backend. Open the terminal link, confirm while signed in, and check the one-use/expired/wrong-account cases. Change the customer email and confirm apply is gated again.
4. Fill the application. Open Terms in a new tab: the original fields must remain. In the original tab, reopen Apply and check only company name/district/division restore. Ensure agreement is initially unchecked and private fields are absent from sessionStorage.
5. Submit with missing fields/consent: values remain, no User/profile is created and draft remains. Correct the form, optionally attach a license, accept Terms and submit: one pending profile, unchanged customer credentials and cleared draft.
6. Verify staff bell/count, pending queue, search/filter, details, private document download and email recipients. A Support/Finance/Catalogue-only user, ordinary customer and nonstaff member of the Partners group must get 403 on review endpoints.
7. Reject with no reason: fail clearly. Reject with a reason: customer receives email/in-app notice and sees it on status. Resubmit as customer: same application ID, pending, one new review notification.
8. Approve as Partners staff: customer gets Partner Company membership and Partner Dashboard link. Verify customer profile/cart and any existing seller flow still work. Repeat the decision: fail, no second audit/notification. Partners staff must not access owner-only Partner financial/suspension/verification actions.
9. Check notification isolation/mark-read; try another user's notification ID or private license as an unauthorized user. Anonymous license downloads must require login. Verify normal public Partner stores/product pages still hide contacts from guests and exclude Partner products from the main marketplace.
10. Test desktop/mobile and both themes. Hard refresh CSS/JS with **Cmd + Shift + R** (Windows/Linux: **Ctrl + Shift + R**). Keep a separate test for existing ledger, invoices and reviews using [agro-partners-setup.md](agro-partners-setup.md).

## 8. Automated checks and known baseline error

```bash
python manage.py test partners dashboard
python manage.py check
python manage.py makemigrations --check --dry-run
```

For SQLite concurrency tests, use a disposable file path; never use your actual `db.sqlite3`:

```bash
ROOTLINE_TEST_DB=/tmp/rootline-partner-tests.sqlite3 python manage.py test --noinput
```

On PowerShell set `$env:ROOTLINE_TEST_DB = 'C:\Temp\rootline-partner-tests.sqlite3'` after creating that directory, run `python manage.py test --noinput`, then `Remove-Item Env:ROOTLINE_TEST_DB`.

Full suite after Flaw 1: **273 tests, 272 passed**. After Flaw 2: **283 tests, 282 passed**. After Flaw 3: **287 tests, 286 passed**. Each run has the same pre-existing error in `reviews.tests.ReviewMigrationTests.test_duplicate_reviews_block_migration_without_deleting_data`: `accounts_user.theme_preference` NOT NULL. It is not suppressed or changed by this task. All 57 Partner tests pass, including the real concurrent decision/completion/invoice/review checks.

Terms inspection before changes found that the old Partner form already used `target="_blank"`; no inability to return was reproduced. Its link was separate from the checkbox, had no visible new-tab hint or `noreferrer`, and the Terms page lacked Back navigation. Customer signup had no Terms checkbox/link, so none was added. No password/file draft storage was introduced.

## Remaining gaps — intentionally not implemented

- Partner dispute handling beyond the existing amount-discrepancy flag/owner ledger adjustment.
- Partner performance metrics and rules for automatic suspension beyond existing overdue-invoice visibility rules.
- Production configuration: `DEBUG`, `ALLOWED_HOSTS`, HTTPS, deployment/email monitoring and a production database. Current settings are not made production-ready by this change.
- Lawyer review and finalization of the draft Partner Terms.
