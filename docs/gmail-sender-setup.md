# Gmail sender: mahinislam020@gmail.com

The sender template now uses `mahinislam020@gmail.com`. The SMTP connection is
already implemented using python-dotenv. `DEFAULT_FROM_EMAIL` also falls back
to `EMAIL_HOST_USER`, so changing the SMTP login does not leave the old sender
as the default. Public contact details are separate from the SMTP sender.

## Finish on your own computer

1. Open a terminal beside `manage.py`, activate your existing virtual
   environment, and install the recorded dependencies if this is a fresh ZIP:

   ```sh
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. Open **`.env` beside `manage.py`**. `.venv` is the Python environment directory;
   email settings do not go inside it. If `.env` is missing, copy `.env.example`
   to `.env`. Keep an existing `DJANGO_SECRET_KEY` and other settings unchanged.
   Private `.env` files are ignored by Git and are not included in GitHub ZIPs.

3. Sign in to **mahinislam020@gmail.com** at
   [Google Account security](https://myaccount.google.com/security), enable
   **2-Step Verification**, then open
   [App passwords](https://myaccount.google.com/apppasswords). Create one named
   `RootLine Django`. Copy its 16 characters without the grouping spaces.
   Use an App Password from this same Google account, not its normal password.
   Paste it only into your private local `.env`; do not send it in chat.

4. Set these lines, with each variable on a separate line:

   ```dotenv
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=true
   EMAIL_HOST_USER=mahinislam020@gmail.com
   EMAIL_HOST_PASSWORD=replace-with-your-own-gmail-app-password
   DEFAULT_FROM_EMAIL=mahinislam020@gmail.com
   ```

   The password above is a placeholder. The private `.env` prepared in the cloud
   workspace has a blank password awaiting your own value; it cannot send mail
   until credentials are supplied. The cloud workspace cannot edit the file on
   your Mac. Keep your stable Django secret; if this is a first setup, generate
   one using the instructions in `docs/account-recovery.md`.

5. Stop the running server with **Ctrl + C**, then start it again:

   ```sh
   python manage.py check
   python manage.py runserver
   ```

   This sender change does not require migrations. Existing process/PyCharm
   environment variables override `.env`; update/remove old `EMAIL_*` overrides
   there if Django still uses console mode or the previous sender.

6. Use Forgot password or Forgot username with the email stored on an active
   RootLine account. That address is the **recipient**; it does not need to match
   the Gmail **sender**. Check Inbox and Spam. The generic confirmation is shown
   even for unknown addresses and throttled requests, so it is not proof of
   delivery. Recovery allows three attempts per address per ten minutes.

If sending fails, inspect the terminal for the SMTP error. Authentication errors
usually mean a wrong-account/incorrect App Password; connection errors can mean
the host blocks SMTP port 587. Check the account email, active status and Spam
before retrying. Console mode prints messages instead of delivering them.
Never paste passwords, complete reset links, or unredacted mail logs into chat.

## Files and verification

- `.env.example`: Gmail SMTP template and requested public sender address;
  contains only a fake password placeholder.
- `rootline/settings.py`: default From address follows the configured SMTP login.
- `docs/account-recovery.md`: Gmail examples updated to the requested sender.
- `docs/gmail-sender-setup.md`: these local setup instructions.
- `.env` (private, ignored, not pushed): prepared SMTP settings and a local stable
  Django secret; Gmail App Password still missing.

All 14 recovery tests and Django system checks passed. The recovery tests use
Django's in-memory mail backend; they do not deliver real mail. Real Gmail
authentication/delivery cannot be verified without your App
Password. No SMTP message was sent during this configuration change.
