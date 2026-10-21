# RootLine contacts — no setup required

The public contact details now work **without environment variables, `.env` files or PyCharm configuration**, locally and after deployment:

- Business: RootLine
- Phone and WhatsApp: +8801923194036
- Email: rootlineuap@gmail.com
- Languages: Bangla, English

They are defined once in the `ROOTLINE_CONTACT_*` section at the bottom of `rootline/settings.py`. All contact pages, footer, header, sheet and order-support links use those settings. Public business details are not authentication secrets.

## What to do

1. Use the updated code from `feature/rootline-contact-system`.
2. Stop your existing Django server and run it again normally: `python manage.py runserver` (or use your existing PyCharm Run button).
3. Open `http://127.0.0.1:8000/contact/`.

For deployment, deploy this updated code and restart/redeploy the web service normally. **No contact-specific hosting environment setup is required.** Existing database, Django secret, static-file and voice setup remain as before. No migration or new package is needed.

If your Mac has a downloaded ZIP rather than a Git checkout, the quickest fix is to open `rootline/settings.py` and replace the five corresponding assignments with:

```python
ROOTLINE_CONTACT_BUSINESS_NAME = os.environ.get('ROOTLINE_CONTACT_BUSINESS_NAME', '').strip() or 'RootLine'
ROOTLINE_CONTACT_PHONE = os.environ.get('ROOTLINE_CONTACT_PHONE', '').strip() or '+8801923194036'
ROOTLINE_CONTACT_WHATSAPP = os.environ.get('ROOTLINE_CONTACT_WHATSAPP', '').strip() or '+8801923194036'
ROOTLINE_CONTACT_EMAIL = os.environ.get('ROOTLINE_CONTACT_EMAIL', '').strip() or 'rootlineuap@gmail.com'
ROOTLINE_CONTACT_LANGUAGES = os.environ.get('ROOTLINE_CONTACT_LANGUAGES', '').strip() or 'Bangla, English'
```

Save, restart the server, and deploy that same saved change. Replace the existing assignments rather than adding duplicates.

## Optional changes later

Non-empty environment variables can override the five public defaults. Missing or blank values use the built-in public details. The [.env.example](../.env.example) is optional, and Django does not read it automatically.

Facebook, Messenger, Instagram, YouTube, other socials, address, support hours and expected reply time remain empty, as requested. Those optional fields stay hidden until configured. The example `yourpage` URLs and example response promises are not published.

Optional settings remain in `rootline/settings.py`:

- `ROOTLINE_CONTACT_FACEBOOK`, `MESSENGER`, `INSTAGRAM`, `YOUTUBE`: full HTTPS URLs. Invalid URLs or URLs containing credentials are hidden.
- `ROOTLINE_CONTACT_SOCIALS`: a JSON list of objects with `label` and HTTPS `url`, up to ten extra channels.
- `ROOTLINE_CONTACT_ADDRESS`: escaped plain text address/service area.
- `ROOTLINE_CONTACT_HOURS`: an explicit Asia/Dhaka schedule, for example `Sat-Thu, 9:00 AM - 8:00 PM (Bangladesh time)`, `Daily, 9:00 AM - 8:00 PM`, or semicolon-separated shifts. Overnight shifts work. A recognized schedule shows a schedule-based availability indicator on each page request; this is not live agent presence. Unsupported text displays without a status claim.
- `ROOTLINE_CONTACT_REPLY_TIME`: your actual reply-time commitment.
- `ROOTLINE_CONTACT_WHATSAPP_MESSAGE` and `ROOTLINE_CONTACT_EMAIL_SUBJECT`: optional prefilled text. Empty uses a friendly RootLine support message/subject.

To change public defaults for every deployment, edit the five assignments in settings once. To remove a built-in channel entirely, remove its public fallback there too; empty settings still produce a graceful FAQ/order-support-only page.

## Privacy and behavior

No messages or calls are initiated automatically. Links open only on a user click; external links use `noopener noreferrer`. No contact form, widget, tracker, map embed or external font was added. Order links include only the order number, not the recipient, address or payment details. Existing URLs/forms/models/business logic remain intact, with the previously added `/contact/` route.

[Contact review and screenshots](contact-review/README.md).
