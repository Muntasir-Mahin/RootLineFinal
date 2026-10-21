# RootLine contact configuration

Contact information has one source: `ROOTLINE_CONTACT_*` settings in `rootline/settings.py`, all read from environment variables with empty defaults. `rootline/contact.py` normalizes/validates these settings for display and links; `site_contact` exposes `contact`, plus the compatible `contact_email` value. Templates contain no configured phone, email or social URL literals.

## Your configured values

| Environment variable | Value |
| --- | --- |
| `ROOTLINE_CONTACT_BUSINESS_NAME` | `RootLine` |
| `ROOTLINE_CONTACT_PHONE` | `+8801923194036` |
| `ROOTLINE_CONTACT_WHATSAPP` | `+8801923194036` |
| `ROOTLINE_CONTACT_EMAIL` | `rootlineuap@gmail.com` |
| `ROOTLINE_CONTACT_LANGUAGES` | `Bangla, English` |

You confirmed that the example Facebook/Messenger URLs, hours and reply time should remain empty. Address, Instagram, YouTube and other socials are also empty. No availability indicator or reply-time promise is published until you configure those fields. Settings defaults remain empty; these public values are supplied in [.env.example](../.env.example), not embedded in Python defaults or templates. They are public contact information, not authentication secrets.

**Django does not automatically read `.env` or `.env.example`.** Use one of the process-environment methods below and restart the server after changes. No dotenv library or PyCharm plugin is required.

## PyCharm: running with the Run button

1. Open the same project checkout you intend to run.
2. In the macOS menu bar choose **Run → Edit Configurations…**.
3. Select your Django/runserver configuration. If there is none, click **+ → Python**, name it `RootLine`, set Script path to this project's `manage.py`, Parameters to `runserver`, Working directory to the project root, and choose this project's `.venv` interpreter.
4. Find **Environment variables** (under **Modify options** if hidden), then open its table editor.
5. Add the five rows above. Enter values exactly as shown, without shell quotes. Keep existing Django, Ollama and Whisper variables.
6. Leave optional contact fields absent or explicitly empty. If you previously set the example URLs or schedule, remove those old values.
7. Click **Apply → OK**, stop the old server, and start this configuration. Open `http://127.0.0.1:8000/contact/`.

For PyCharm's single-line environment field, paste:

```text
ROOTLINE_CONTACT_BUSINESS_NAME=RootLine;ROOTLINE_CONTACT_PHONE=+8801923194036;ROOTLINE_CONTACT_WHATSAPP=+8801923194036;ROOTLINE_CONTACT_EMAIL=rootlineuap@gmail.com;ROOTLINE_CONTACT_LANGUAGES=Bangla, English
```

Terminal exports do not update a server launched separately by PyCharm's Run button.

## macOS/Linux terminal: runserver from the same shell

From your actual project directory:

```sh
cp .env.example .env
source .venv/bin/activate
set -a
source .env
set +a
python manage.py runserver
```

`.env` is ignored by Git. `.env.example` is intentionally committed. The example is valid shell syntax; quoted values with spaces become plain values in the process environment.

## Production

For a hosting dashboard (Render/Railway/container platform or similar), open the web service's **Environment variables** settings, add the same five key/value rows above (without quotes), save and restart/redeploy the web service. Keep the existing database, Django secret and voice configuration. Optional fields are separate environment variables; absent values hide those channels.

For Docker Compose, copy `.env.example` to a server-owned contact file and add it to the **existing web service**:

```yaml
services:
  web:
    env_file:
      - ./contact.env
```

Keep existing service configuration/env files alongside this entry. Recreate the web service with `docker compose up -d --force-recreate web`. Compose's project `.env` alone is used for interpolation; `env_file` injects these values into the running container. Run your normal CSS build and `collectstatic` release steps.

For an existing Gunicorn/systemd deployment:

1. Copy the example contents to `/etc/rootline/contact.env` on your server, retaining the public values above and your selected optional values.
2. Run `sudo systemctl edit rootline.service` (replace `rootline.service` with your actual existing service name) and add:

   ```ini
   [Service]
   EnvironmentFile=/etc/rootline/contact.env
   ```

3. Run `sudo systemctl daemon-reload` and `sudo systemctl restart rootline.service`.

The file is an environment file, not an application import. Do not place credentials in a public static directory. No production deployment was performed by this change.

## Optional settings and behavior

All following fields default to empty:

- `ROOTLINE_CONTACT_FACEBOOK`, `ROOTLINE_CONTACT_MESSENGER`, `ROOTLINE_CONTACT_INSTAGRAM`, `ROOTLINE_CONTACT_YOUTUBE`: full HTTPS URLs. Invalid schemes/URLs and URLs containing credentials are hidden.
- `ROOTLINE_CONTACT_SOCIALS`: JSON list of objects with `label` and HTTPS `url`; at most ten extra channels. Missing labels, invalid URLs and malformed JSON are ignored. Do not enter template syntax.
- `ROOTLINE_CONTACT_ADDRESS`: address or service area. Plain text only; line breaks are preserved and HTML is escaped.
- `ROOTLINE_CONTACT_HOURS`: optional schedule text, interpreted in **Asia/Dhaka**. Supported formats are `Sat-Thu, 9:00 AM - 8:00 PM (Bangladesh time)`, `Daily, 9:00 AM - 8:00 PM`, or semicolon-separated shifts such as `Sat-Thu, 9:00 AM - 8:00 PM; Fri, 10:00 AM - 1:00 PM`. Three-letter day names, 12-hour times and optional Bangladesh-time suffix are supported. Overnight shifts are supported. Equal opening/closing times are not treated as a 24-hour promise.
- A recognized schedule shows `Available now` during its hours, or the next opening time/day when closed. This is schedule-based, **not live agent presence**, and is calculated on each page request. Arbitrary/unrecognized hours text is displayed without an availability claim. Empty hours hide both hours and availability.
- `ROOTLINE_CONTACT_REPLY_TIME`: plain text reply-time commitment; empty hides it.
- `ROOTLINE_CONTACT_LANGUAGES`: plain text display (currently `Bangla, English`). This adds no translation switch.
- `ROOTLINE_CONTACT_WHATSAPP_MESSAGE`: optional default message. Empty uses `Hello RootLine, I need help.` (with the configured business name).
- `ROOTLINE_CONTACT_EMAIL_SUBJECT`: optional subject. Empty uses `RootLine support` (with the configured business name).

Bangladesh numbers may be `01XXXXXXXXX`, `+8801XXXXXXXXX`, `8801XXXXXXXXX` or `008801XXXXXXXXX`, with spaces/dashes/parentheses. Display is `+880 1923-194036`; telephone uses `tel:+8801923194036`; WhatsApp uses digits only. Invalid numbers hide their channels. Other structurally valid international E.164 numbers are also accepted; this does not verify ownership or reachability.

## UI and privacy

`/contact/` is named `contact`; existing routes are retained. Shared `contact_card.html` and `contact_channels.html` render the full page, help cards, footer, modal sheet and order help. Empty configuration leaves FAQ and order-support routes without empty icons or dead channel links. A desktop support bar and mobile drawer expose the configured direct contact channels. The sheet is a native modal: background inert, focus cycles inside, Escape/close/backdrop dismiss, and focus returns to the trigger. Copy uses the existing toast, including within the modal; clipboard denial provides manual-copy guidance.

Order-success, customer/seller orders, checkout, auction checkout, payment and customer/seller dispute templates receive a small support box **outside existing forms**. Existing order numbers are appended to WhatsApp text and email subjects. Checkout has no order number yet, so its message stays generic. The links contain no recipient address, payment ID or order contents. The dispute link goes to the existing authenticated My orders flow, which enforces order access and eligibility.

Contact links do not send messages automatically. External destinations open only on a user click, in a new tab with `noopener noreferrer`. No external fonts, widgets, trackers, iframes, map embeds, network calls or contact form were added. 404/500 templates did not exist, so they were skipped as requested. Models, migrations and business forms/services were not changed.

## Build and verification

```sh
npm ci
npm run build:css
npm run check:design
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test rootline.test_contact rootline.test_site
```

The final browser screenshots and results are under [contact-review](contact-review/README.md).
