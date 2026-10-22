# Agro Partners: setup and owner guide

This branch adds a separate `partners` app. Partner products never use the existing marketplace `Product`, search, cart or checkout. Buyers send Order Requests and pay companies directly; RootLine does not process those payments or deliveries. The existing `accounts.User` model is unchanged: a Django **Partner Company** group plus a one-to-one company profile identifies the new account type.

Complete per-phase file lists and reasons: [partners-phases.md](partners-phases.md).

## 1. Open the project and install packages

Open the folder containing `manage.py`. Use Python 3.12 or newer, supported by Django 6.1.2. With a new ZIP, create a virtual environment; keep an existing working environment if you already have one.

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The existing requirements already contain `Django==6.1.2`, `Pillow==12.3.0` and `python-dotenv==1.2.4`. No new Python dependency is needed. If installing individually:

```bash
python -m pip install Django==6.1.2 Pillow==12.3.0 python-dotenv==1.2.4
```

Do not replace the project's requirements with a freeze of unrelated packages. They are already up to date for this feature.

## 2. Keep your local configuration and database

`.env` is a **file beside `manage.py`**. `.venv` is a different thing: the Python environment folder. Neither `.env.example` nor `.venv` is where live SMTP settings should be edited.

Keep your existing working `.env`, `db.sqlite3`, `media/` and, after this feature is used, `private_partner_files/`. A downloaded GitHub ZIP does not include these ignored local files. Back them up before replacing a working project. Do not recreate your Gmail App Password simply because you downloaded another ZIP.

If `.env` does not exist, copy `.env.example` to `.env`. Replace its secret placeholder with the output of:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Keep `DJANGO_SECRET_KEY` stable between restarts; changing it invalidates sessions and password-reset tokens. Put each variable on its own line. For a local console-only email test:

```dotenv
DJANGO_SECRET_KEY=paste-your-generated-secret-here
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-sender@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-sender@gmail.com
```

These are placeholders. The console backend prints messages in the runserver terminal; it does **not** deliver mail. To send mail, keep your existing verified SMTP setup and use `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, with the same real sender in `EMAIL_HOST_USER` and `DEFAULT_FROM_EMAIL` and that sender's Gmail App Password. Restart Django after editing `.env`. Never commit real credentials or show them in screenshots.

Partner notifications use this existing backend: approval/rejection, new Order Request, and acceptance/decline. Empty SMTP credentials skip delivery, and delivery errors are logged without rolling back a sale. This feature does not verify deliverability or send marketing emails. Console messages are useful for development; check the server logs if an SMTP message does not arrive.

## 3. Apply the new migrations and create an owner

Back up your existing database first. Then:

```bash
python manage.py migrate
python manage.py check
```

Migrations create only Partner tables and seed the editable **Standard Partner Plan** (5% commission, no fixed/minimum fee). They do not alter `accounts.User` or existing marketplace tables. Use the committed migrations; do not run `makemigrations` as a setup step.

If you do not already have an owner account:

```bash
python manage.py createsuperuser
```

The existing owner-only Django admin requires an active staff superuser. Company users do not get Django admin access.

## 4. Understand uploads and Tailwind

The project already has:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Keep those existing settings. In development, the existing URL configuration serves media with `DEBUG=True`. Company logos, covers, gallery images and product images use subdirectories under `media/partners/`. Certificates accept JPG/PNG/WebP or a PDF. Each file is limited to 5 MB; images must be below 16 megapixels, are re-encoded, stripped of metadata and resized to at most 2400 pixels. Galleries allow 12 images, and products allow 6 extra images.

Payment screenshots are **different**: `private_partner_files/payment-proofs/` is outside public media. Only the corresponding company and the owner can download them through an authenticated route. Do not configure your web server to serve `private_partner_files/` publicly. Both public uploads and private payment evidence need persistent storage and backups; GitHub does not back them up.

Partner pages extend `base.html` and use the existing theme/product-card classes. Extra Tailwind utilities are compiled and scoped to `.partner-pages`, without changing global CSS. The compiled asset is committed, so Node is not needed just to run the site. If you edit Partner templates and introduce new utilities:

```bash
npm ci
npx tailwindcss -c partners/tailwind.config.js -i partners/static/partners/source.css -o partners/static/partners/partners.css --minify
```

Do not rebuild unrelated global styles for a Partner-only change. Hard-refresh after CSS updates: **Cmd + Shift + R** on macOS, **Ctrl + Shift + R** on Windows/Linux.

## 5. Start Django and register a company

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/partners/`. Choose **Register as a Partner Company**. Supply a company name, email, password, phone, address, district/division and optional trade license; accept the Partner Terms.

This creates a separate account, not a conversion of an existing buyer/seller. Use **Partner Company Login** at `/partners/login/` with the company email and password. Registration returns the same generic message for duplicates. Partner-company names and login emails are unique ignoring case; normal user email rules are unchanged.

A pending company can edit its profile and assets but cannot publish products or appear publicly. The internal username is generated; company login uses email. Existing password recovery can also recover these accounts by email.

The Terms are clearly marked **Draft v1: must be reviewed by a lawyer**. They describe fees, direct sales, accurate reporting, audit rights, non-payment suspension and fake reviews. The registration stores the acceptance time/version.

## 6. Approve the company and prepare its store

1. In another browser/profile, sign in at `/admin/` as the owner.
2. Under **Partners → Company profiles**, select the company and choose **Approve selected Partner Companies**.
3. Rejection requires a reason in the action form. Verification is a separate action; approval does not automatically award a verified badge. Suspension/unsuspension also requires a reason.
4. Add product categories under **Partner categories**. These do not affect main marketplace categories.
5. In the company dashboard, edit the profile: logo/cover, tagline, About us, established year, one Why choose us reason per line, categories, website/social/map links and optional employees/farmers counts. Add achievements, certifications and gallery images.
6. Add a company product with a category, price, optional lower discount price, unit, stock, description and image. Manage extra images from the product list. Hide/unhide or edit products there. Products referenced by orders are protected from deletion; hide them instead.
7. Open the Partner Store from the dashboard. The auto-generated slug remains stable after renaming. Products are available only inside this store and its detail pages.

Phone, email, street address and contact links are rendered only to logged-in visitors; district/division are public. Avoid putting private contacts into public free-text About/product/review fields or public upload captions.

## 7. Configure commission, subscription and payment instructions

In `/admin/` → **Partners → Billing plans**, edit the seeded plan or create another active plan. Keep one active default. Configure:

| Setting | Meaning |
| --- | --- |
| Commission rate | Percentage of the final recorded ledger sales, including manually reported sales. Default is 5%. |
| Commission only | Monthly fee = monthly sales × rate, subject to minimum monthly fee. |
| Subscription only | Fixed monthly fee, or annual fee in the approval/subscription anniversary month. |
| Higher of fixed fee or commission | Monthly plan: larger of monthly fixed fee or monthly commission. Annual plan: charge the annual floor once, then invoice commission exceeding fees already invoiced in that annual cycle. |
| Minimum monthly fee | A floor on every generated monthly invoice, including months of an annual plan. Leave 0 if that is not intended. |
| Due days | Calendar days after month-end before payment is due. Default 14. |
| Grace days | Days from the due date until automatic public hiding; 0 means hiding the day after the due date. Default 7. |
| Payment instructions | Your platform-fee bKash/bank instructions. These are displayed in the company's billing page and frozen on each invoice. No payment API is connected. |

Examples: ৳10,000 sales at 5% produce ৳500 commission. A monthly subscription of ৳300 produces ৳300. A monthly higher-of plan with ৳300 fixed fee produces ৳500 for those sales, or ৳300 when the commission is only ৳100. For an annual higher-of plan with a ৳1,200 floor: charge ৳1,200 initially; later cumulative commission of ৳1,500 creates another ৳300 charge, not another ৳1,500.

Under **Company billing settings**, assign a plan and optionally override rate/mode/fee/period/minimum/due/grace per company. Blank numeric overrides inherit the plan; **0 is an explicit override**. An optional subscription start changes the annual anniversary. **Pause billing** skips new generation; it does not erase old unpaid invoices. Company staff cannot change any of these settings.

There is no proration: the approval month counts as a full billing month. New invoices snapshot policy, due/grace dates and payment instructions; editing a plan does not rewrite issued policy. Keep annual-plan changes aligned with anniversary dates and review historical adjustments with the owner.

## 8. Generate and verify invoices

Generate the **previous calendar month**:

```bash
python manage.py generate_partner_invoices
```

Or select a month, optionally one company by its admin ID:

```bash
python manage.py generate_partner_invoices --month 2026-10
python manage.py generate_partner_invoices --month 2026-10 --company 1
```

Replace examples with a real month at/after approval and not in the future. The same company/month cannot get duplicate invoices. Running again refreshes **unpaid** totals from the ledger with the original issued policy. Annual hybrid plans backfill earlier months in the annual cycle before charging a later month.

Alternatively, select companies in admin, use **Generate monthly Partner invoices**, and optionally enter `YYYY-MM` in the action form's month field. Blank means the previous month. Wait until month-end for real billing; generating a current-month invoice is useful for demonstration but includes incomplete sales.

The company opens **Company billing & invoices**, reads instructions, pays the platform fee externally and submits a transaction/reference, optionally with a screenshot. A submission does **not** mark the invoice paid. The owner checks real receipt of funds, selects the invoice in admin, adds a verification reason, and chooses **Verify invoice paid**.

Paid invoices are frozen. Zero-amount invoices are automatically settled without a transfer. If sales are added/adjusted after a month is settled, the ledger is flagged for **owner reconciliation**; a paid invoice is never silently rewritten. Credit notes or automated carry-forward adjustments are not included: the owner must reconcile those cases using the audit trail and actual payments. Do not use an early zero invoice as a final close of an unfinished month.

Unpaid invoices warn the company after the due date. At the grace date the directory, store, product and order-request URLs are hidden publicly (404). Company dashboards remain available for payment and resolving existing orders. Verified payment restores public visibility unless another restriction applies.

Company-profile **Visibility override** supports **Hide store** or **Bypass billing suspension**. A bypass never overrides pending/rejected/inactive/admin-suspended status. All owner changes and significant order/ledger/billing/review actions are audited.

## 9. Schedule billing

On a Linux server run `crontab -e`. Replace `/srv/RootLineFinal` with your actual absolute project path:

```cron
# Generate the previous month's invoices at 02:15 on the first of each month.
15 2 1 * * cd /srv/RootLineFinal && /srv/RootLineFinal/.venv/bin/python manage.py generate_partner_invoices >> /srv/RootLineFinal/partner-billing.log 2>&1
# Record newly overdue status changes each day at 02:30.
30 2 * * * cd /srv/RootLineFinal && /srv/RootLineFinal/.venv/bin/python manage.py update_partner_billing >> /srv/RootLineFinal/partner-billing.log 2>&1
```

Cron uses the server's timezone; Django dates use the existing `Asia/Dhaka` setting. Configure the server/scheduler timezone as intended. Public hiding also checks dates live, so it does not depend on cron changing the status first. Cron is still needed to create invoices. Keep the scheduler running when the site is deployed.

Simple alternative: run `generate_partner_invoices` manually once per month and `update_partner_billing` daily, or configure these exact commands in your hosting provider's scheduled jobs / Windows Task Scheduler. Avoid scheduling an interactive terminal session on a laptop that is usually off.

## 10. Owner reporting and moderation

In **Partners → Invoices**, use the **Billing report**, **Export ledger CSV** and **Export invoice CSV** links. The report shows monthly calculated commission separately from actual platform fees, outstanding invoice totals, top companies, flagged entries and manually reported phone sales. These pages/exports are owner-only.

Under **Sales ledgers**, choose **Adjust / review with reason**. Companies cannot edit/delete completed ledger entries; owner adjustments retain the original amount and append old/new amount, reason and actor. An adjusted sale loses buyer-confirmed evidence; the owner cannot claim a buyer confirmation on the buyer's behalf. Confirmations after an amount dispute stay blocked pending owner review.

Under **Company reviews**, the owner can hide/restore selected reviews with a reason. Hidden reviews and their replies are excluded from public averages, counts and breakdowns. Reports are visible under **Review reports**. Company users can post only one public reply through their own dashboard; they cannot hide or edit a buyer review.

## 11. Manual full-flow checklist

Use separate browser profiles/incognito windows for company, buyer and owner:

1. Check normal marketplace search/cart/checkout still work. Partner products must be absent there.
2. Register a company; verify Terms are required. Pending company can log in/edit, but product publishing is denied and its public URL returns 404.
3. Approve as owner, add Partner categories, complete profile/assets and add a discounted product with stock. Check directory filters, store search/sorting/pagination and product detail on desktop/mobile and both themes. Card hover should match existing products.
4. Sign out: contacts must be absent from HTML, not merely visually hidden. Sign in as buyer: contacts appear. A normal buyer/seller must not access company dashboards.
5. Place an Order Request with quantity, address and phone. Before acceptance, company sees no buyer phone/address; after acceptance, it does. Acceptance reserves stock; cancellation restores it. Try a second company's IDs: edits/orders/invoices/replies must be refused.
6. Complete the accepted order. The form defaults to quantity × the requested discounted price. Change the final amount: saving without a reason must fail. Saving with a reason creates one ledger entry; retries must not create another. Payment/delivery take place directly with the company.
7. As buyer, confirm received and check the Buyer-confirmed label. On a different test order, dispute the amount; owner report should flag it. Owner adjusts with a reason and reviews the retained original amount/audit records.
8. Report a phone sale through the company ledger page. Owner sees it marked **Manually reported**; it has no verified buyer evidence and cannot produce a review.
9. Generate the month's invoice twice. Check one invoice, correct sales/commission and policy, and view Billing as company. Test all three modes with separate plans/companies; use a nonzero fixed fee and a minimum to see their effects.
10. Submit an external payment reference and optional screenshot; invoice must stay unpaid until owner verification. Another company and anonymous visitor must not download the proof. Verify actual payment as owner, entering a reason, then mark paid.
11. To test overdue hiding without editing financial records manually, generate an older eligible invoice for a company approved in that month, or use a disposable test database. Past the grace date, public routes return 404 but company Billing works. Test owner bypass, verified-payment restoration and an independent admin suspension.
12. As a buyer with a completed order, open **My Partner Order Requests → completed order → Leave a verified purchase review**. Submit 1–5 stars, title and comment. Requested/accepted/cancelled/declined orders and other buyers cannot review; one completed order allows one review. A company cannot order/review itself.
13. Check directory average/count, store breakdown and Verified purchase labels. As company, post one public reply; a second reply must fail. As another logged-in user, report the review; owner can hide it with a reason and rating statistics must update.
14. Review console notification output; if already using real SMTP, check inbox/spam and server logs. Check audit events, CSV exports and the monthly scheduler. Finish by hard-refreshing **Cmd + Shift + R**.

## 12. Automated verification and production notes

```bash
python manage.py test partners
python manage.py check
python manage.py makemigrations --check --dry-run
npm run check:design
```

To include real concurrent submission tests on SQLite, use a disposable **file-backed** test database. This path is for tests only; never point it at `db.sqlite3`:

```bash
# macOS/Linux
ROOTLINE_TEST_DB=/tmp/rootline-partners-tests.sqlite3 python manage.py test partners --noinput
```

```powershell
# Windows, after creating C:\Temp if needed
$env:ROOTLINE_TEST_DB = 'C:\Temp\rootline-partners-tests.sqlite3'
python manage.py test partners --noinput
Remove-Item Env:ROOTLINE_TEST_DB
```

37 Partner tests pass, including concurrent completion/invoice/review, isolation, privacy, permissions, fee modes and moderation. The complete repository run has 267 tests: 266 pass and one existing `reviews.tests.ReviewMigrationTests.test_duplicate_reviews_block_migration_without_deleting_data` errors on the old `accounts_user.theme_preference` NOT NULL constraint. That unrelated migration test was left unchanged to respect scope.

Before production, configure `DEBUG=False`, explicit `ALLOWED_HOSTS`, HTTPS, secure cookies and a stable secret in deployment configuration; collect static files with `python manage.py collectstatic` and serve static/public media through your production server/storage. The existing project does not read `DEBUG`/`ALLOWED_HOSTS` from `.env`; merely adding those variable names will not change them. Do not expose your development server or private evidence folder. Keep databases and both upload locations backed up. Use a real transactional email provider and proper SPF/DKIM for a custom sending domain.

Review throttling is 10 attempts per buyer per hour using Django cache. The existing local-memory cache provides basic protection per process; use a shared cache such as Redis and gateway limits for a multi-worker production deployment. Profile/product/review content is plain escaped text; HTML is not enabled. The feature is a recording/verification workflow, not an independent proof that a sale occurred or money arrived.

## Recommended later upgrades

- PostgreSQL, background notification jobs/retries and shared rate limits for scale.
- Formal credit notes, frozen billing periods, prorated plan changes and automatic reconciliation of late adjustments.
- Owner dashboards for report resolution, stronger fraud detection and document verification.
- Order attachments, expiry/reminders and stock-reservation expiry rules.
- Private object storage with retention rules, upload malware scanning and monitoring.
- Lawyer-reviewed/versioned Partner agreements and explicit acceptance of later rate changes.
