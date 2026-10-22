# Password and username recovery setup

Only account recovery is added. Existing sign-in, signup, logout, user models,
styles and unrelated views are unchanged. The login template gains one line
containing the two links. All six recovery pages extend `base.html` and reuse
existing form components and CSS classes. The three email templates are plain
text, so they deliberately do not inherit the site's HTML layout.

The custom model inherits `email` from `AbstractUser`; `USERNAME_FIELD` is
`username`. Email is optional and non-unique. The model remains unchanged:
accounts without an email cannot use recovery; a shared email receives a reset
link for each active account with a usable password, or one username email
listing all active accounts. Making email required or unique is a separate
change requiring existing-data review, a migration and signup/profile validation.

## 1. Install the Python packages

Open a terminal in the directory containing `manage.py`. Use Python 3.12 or
newer and activate your existing virtual environment. If you need a new one:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\Activate.ps1` instead. In PyCharm,
select this virtual environment as the project interpreter, then reopen its
terminal. Run:

```sh
python -m pip install -r requirements.txt
```

The supplied `requirements.txt` records all runtime dependencies found in this
project: `Django==6.1.2`, `Pillow==12.3.0`, and `python-dotenv==1.2.4`.
The exact command for installing just the new package into an otherwise prepared
environment is `python -m pip install "python-dotenv==1.2.4"`. No npm change is
required. Keep the new dependency in requirements when deploying.

## 2. Create a private .env file

If `.env` does not already exist, copy `.env.example` to `.env` beside `manage.py`.
If it exists, add only the missing recovery variables; preserve its other values.
`.gitignore` already ignores `.env`, so no ignore-file change was necessary.
Never commit `.env`, paste credentials into chat, or put passwords in settings.

Use this initial example. Its credentials are fake and console mode sends no mail:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-sender@gmail.com
EMAIL_HOST_PASSWORD=replace-with-your-gmail-app-password
DEFAULT_FROM_EMAIL=rootlineuap@gmail.com
DJANGO_SECRET_KEY=replace-with-a-locally-generated-secret
```

Generate a real Django secret locally:

```sh
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Paste the generated value into `.env` as `DJANGO_SECRET_KEY='your-generated-value'`,
using single quotes to preserve special characters. Generate it once and retain
it across restarts and all application workers. An unstable secret invalidates
reset links and sessions. Do not use the example placeholder as a real secret.

`python-dotenv` loads `.env` on startup. Existing process environment values take
precedence, so also check PyCharm's run configuration or your hosting settings
if changes in `.env` appear to be ignored. Restart Django after editing values.

## 3. Create a Gmail App Password

1. Sign into the Google account `rootlineuap@gmail.com`, which must be an account
   you control.
2. Open [Google Account security](https://myaccount.google.com/security).
3. Under **How you sign in to Google**, turn on **2-Step Verification** and
   complete Google's setup.
4. Open [App passwords](https://myaccount.google.com/apppasswords), sign in again
   if prompted, and create an app password named `RootLine Django`.
5. Copy the generated 16-character password into your private `.env` as
   `EMAIL_HOST_PASSWORD`. Remove the visual grouping spaces. This is an App
   Password, not your ordinary Google password.
6. Set `EMAIL_HOST_USER=rootlineuap@gmail.com` and
   `DEFAULT_FROM_EMAIL=rootlineuap@gmail.com`. Keep console mode until step 5.

Google may hide App Passwords for managed accounts, Advanced Protection, or some
2-Step Verification configurations. Ask your Google administrator or use a
transactional email provider rather than disabling account protection.

Alternatives use the same SMTP backend and environment variable names:

| Provider | EMAIL_HOST | EMAIL_HOST_USER / EMAIL_HOST_PASSWORD |
| --- | --- | --- |
| Brevo | `smtp-relay.brevo.com` | SMTP login and SMTP key shown in Brevo |
| SendGrid | `smtp.sendgrid.net` | `apikey` and your restricted SendGrid API key |
| Mailgun | `smtp.mailgun.org` or the regional host from its dashboard | Domain SMTP username and SMTP password |

Use port `587` and `EMAIL_USE_TLS=true` for these STARTTLS configurations. Set
`DEFAULT_FROM_EMAIL` to a sender verified by that provider. SMTP credentials can
differ from the provider's website password. Follow the provider's current
dashboard for the exact regional hostname and sender requirements.

## 4. Check the application and database

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

These features do not change models or add migrations. `migrate` only applies
existing pending migrations, which matters for a new checkout. Do not generate
a user-model migration for recovery. Existing accounts need an email set through
their current signup/profile form or owner administration, and must be active.

## 5. Test console email, then enable SMTP

Keep `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` and start:

```sh
python manage.py runserver
```

Use the site's normal local development address and follow step 6. Email bodies
print in the terminal running Django, not in a real inbox. Copy the complete
reset URL from that terminal into the same browser. Use your existing account
and do not post reset URLs or console email contents publicly.

Once console recovery works, change only the backend in `.env`:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

Confirm your real sender and App Password are set as described in step 3, then
restart Django and repeat the flows with a mailbox you control. SMTP requires
outbound TCP access to the configured host on port 587. In a restricted cloud
environment, an HTTPS domain allowlist alone does not grant SMTP access; your
host/network administrator may need to allow that connection. Real Gmail
delivery was not tested here because credentials were not supplied.

Compatibility note: Django 6.1.2 rejects combining an explicit `MAILERS` setting
with the requested legacy `EMAIL_*` settings. The old console-only `MAILERS`
block was replaced with the requested `EMAIL_*` configuration. Console remains
the default. These settings are supported but deprecated in 6.1; migrate this
configuration to `MAILERS` before upgrading to Django 2028. Do not add both.

## 6. Manually exercise both flows

1. Register or use an **active** account with an email address you control. Note
   its username, email and current password. Sign out through the existing flow.
2. Open Login and select **Forgot password?**. Enter the account's email. You
   should see exactly: **If an account with that email exists, we have sent an
   email.** Try different letter casing to confirm matching works.
3. Find the console email or inbox message and open its reset URL. Enter the
   same new password twice. Weak/mismatched passwords should show normal Django
   form errors; a valid password should show the completion page.
4. Return to Login and sign in with the original username and new password.
   The old password must fail. The used reset URL must no longer work. Links
   expire after 3 days; use a fresh email if necessary.
5. Sign out. Select **Forgot username?**, enter the same email and verify the
   same generic confirmation. The email should list the active username(s)
   associated with that email; no usernames should appear on the public page.
6. Submit a valid but unregistered email address to each form. Both should
   display the same generic message as the known-address case and send no mail.
   An inactive account must also receive no recovery email.
7. If several active accounts share an address, username recovery lists them
   together. Password recovery sends a separate, account-specific link for each
   active account with a usable password; choose the intended account's email.
8. Check the built-in basic throttle: the two endpoints share a limit of three
   valid recovery submissions per email and ten per client IP in ten minutes.
   Throttled requests show the same generic confirmation and send no mail. Wait
   ten minutes before testing again after hitting the limit. These count
   submissions, not individual outgoing emails for shared addresses.

The throttle uses Django's existing cache with no new dependency. With the
default local-memory cache, limits are per process and reset on restart. For
multiple production workers, configure a shared cache and/or ingress rate
limiting. The code reads `REMOTE_ADDR` and ignores client-supplied forwarded-IP
headers. Configure your trusted proxy to supply the correct client address;
otherwise clients behind it may share one limit. Synchronous built-in email
delivery can still have timing differences; the generic response is not a
claim of timing indistinguishability.

Run the focused automated checks (the test email backend sends no real mail):

```sh
python manage.py test accounts.test_recovery accounts.tests --noinput
```

Validation on Django 6.1.2: all 22 focused tests passed (14 new recovery tests
and 8 existing logout tests). The previous full file-backed suite ran 229 tests:
228 passed and the one previously documented error remains in
`reviews.tests.ReviewMigrationTests.test_duplicate_reviews_block_migration_without_deleting_data`
(`accounts_user.theme_preference` NOT NULL). That unrelated historical-model
test was not changed or disabled. Django system checks, migration drift checks,
dependency consistency and the existing design check passed. SMTP settings
were checked with fake credentials without opening a network connection;
real Gmail delivery still needs your own configuration and end-to-end test.

## 7. Troubleshoot common problems

| Problem | What to check |
| --- | --- |
| No email appears | In console mode, read the Django terminal. In SMTP mode, check the address on the active account, inbox/spam, sender verification, and the three-per-email/ten-per-IP throttle. Unknown/inactive accounts intentionally send nothing. Read server logs for delivery failures; the public message stays generic. |
| SMTP connection times out | Check outbound TCP 587, firewall/hosting restrictions, and the provider's hostname. The application uses a ten-second email timeout. An HTTP proxy does not itself provide SMTP connectivity. |
| SMTP authentication fails (often 535) | Use the full Gmail address and its App Password, not the ordinary account password. Confirm 2-Step Verification, remove spaces around the App Password, restart Django, and check whether exported variables override `.env`. Changing your Google password can revoke App Passwords. Never disable TLS verification. |
| Email goes to spam | Use an approved sender, check Spam/Promotions, avoid mismatched From addresses, and configure SPF/DKIM for your verified custom domain. Gmail quotas and reputation can make a transactional provider more appropriate. |
| Reset link is invalid/expired | Copy the complete URL; it lasts 3 days and becomes invalid after a successful password change. Keep `DJANGO_SECRET_KEY` stable on every worker and restart. Use the newest link, check server time, and request a fresh link after expiry. |
| Reset URL has the wrong domain or HTTP scheme | Django builds it from the incoming request. Use the intended hostname and an explicit `ALLOWED_HOSTS` list. Correct the proxy's Host forwarding. Behind a trusted TLS proxy, configure Django's secure-request handling only when the proxy strips spoofed headers. `ALLOWED_HOSTS` validates the Host header; it does not select or rewrite the domain. |
| DisallowedHost error | Add the exact legitimate local or production hostname to `ALLOWED_HOSTS`, without a scheme or path. Avoid `'*'`. Restart Django. |
| MAILERS/EMAIL_* configuration error | Do not define `MAILERS` alongside these legacy `EMAIL_*` settings on Django 6.1.2. The provided settings use only the requested legacy configuration. |

## 8. Before production deployment

Configure deployment settings separately; this feature does not change them:

1. Set `DEBUG=False`, set `ALLOWED_HOSTS` to your exact public domain(s), and
   retain a private, stable `DJANGO_SECRET_KEY` shared by all workers.
2. Serve the application over HTTPS, enable secure session/CSRF cookies and
   appropriate HTTPS redirects, and configure only trusted reverse-proxy headers.
   Reset links should start with `https://` and your correct public hostname.
3. Store SMTP secrets in the hosting secret store or a private untracked `.env`.
   Set SMTP mode explicitly and verify delivery after deployment. Do not expose
   console email output, reset tokens or credentials in public logs.
4. Prefer a verified transactional sender/provider for production volume. If
   using a custom domain, add the provider's SPF and DKIM DNS records, then
   configure DMARC. Do not try to manage Google's `gmail.com` DNS.
5. Configure shared/ingress abuse protection as described above. Users with
   blank email fields need an appropriate separate support process; making
   email required/unique was intentionally left for a separate decision.
6. Run `python manage.py check --deploy` with production settings and resolve
   the relevant deployment warnings. Test the flows from the public HTTPS URL.

## Changed-file inventory

| File | Reason |
| --- | --- |
| `accounts/recovery_forms.py` (new) | Username recovery email form. |
| `accounts/recovery_views.py` (new) | Built-in reset view integration, shared basic throttle, and active-user username recovery email. |
| `accounts/urls.py` | Register the four password routes and two username routes. |
| `accounts/templates/accounts/login.html` | Add only the two recovery links using existing CSS classes. |
| `accounts/templates/accounts/password_reset_form.html` (new) | Email entry page. |
| `accounts/templates/accounts/password_reset_done.html` (new) | Generic confirmation page. |
| `accounts/templates/accounts/password_reset_confirm.html` (new) | New-password form and invalid-link state. |
| `accounts/templates/accounts/password_reset_complete.html` (new) | Password-change success page. |
| `accounts/templates/accounts/password_reset_email.txt` (new) | Account-specific reset-link email. |
| `accounts/templates/accounts/password_reset_subject.txt` (new) | Single-line reset email subject. |
| `accounts/templates/accounts/username_recovery_form.html` (new) | Username recovery email entry page. |
| `accounts/templates/accounts/username_recovery_done.html` (new) | Generic username recovery confirmation. |
| `accounts/templates/accounts/username_recovery_email.txt` (new) | Email listing matching active usernames. |
| `accounts/test_recovery.py` (new) | Recovery, privacy, CSRF, throttling, token and login regression tests. |
| `rootline/settings.py` | Load `.env`; configure email and three-day reset expiry. |
| `.env.example` | Fake SMTP values and a stable-secret placeholder. |
| `requirements.txt` (new) | Record Django/Pillow runtime requirements and the new python-dotenv dependency. |
| `docs/account-recovery.md` (new) | Setup, manual tests, troubleshooting and file inventory. |

`.gitignore` already ignores `.env` and was not changed. No model, migration,
existing view/form, stylesheet, base template or dependency lockfile was changed.
