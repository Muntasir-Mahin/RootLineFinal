# RootLine contact system: review

Implemented on `feature/rootline-contact-system`, based on the current marketplace-first foundation. This task does not continue or approve the pending marketplace stages 3–7.

- New public **`/contact/`**, URL name `contact`, with responsive channel cards, FAQ/order support, optional address/socials, languages and seller access note.
- Shared contact cards used in the page, compact Help section, footer Support column, modal quick-contact sheet and order support boxes.
- Desktop phone/contact utility bar; contact links in the account menu and mobile drawer.
- Native modal sheet with a full-width mobile bottom sheet, focus cycling, background inert, Escape/button/backdrop dismissal and trigger focus restoration. The existing toast temporarily moves inside the modal so Copy feedback remains visible and accessible.
- Bangladesh/international number normalization, encoded WhatsApp messages and mailto subjects, safe optional HTTPS socials. Phone and email Copy actions handle clipboard permission denial honestly.
- Order-help links add the order number to WhatsApp and email only when an order exists. No recipient, address, payment ID or item contents enter contact links. Checkout remains generic until an order is created.
- Public phone, WhatsApp, email, name and languages now have built-in defaults; optional fields remain empty; old `contact_email` remains available. FAQ/order support remains usable with no configured channels. No contact form, external widget, tracking, iframe, external font or automatic message sending.

## Configured versus intentionally empty

Phone and WhatsApp use `+8801923194036`; email is `rootlineuap@gmail.com`; name is RootLine; languages are Bangla, English. They are now public defaults in `rootline/settings.py`, with optional non-empty environment overrides. No `.env` file or contact-specific PyCharm/production configuration is required. Templates still contain no phone, email or social URL literals.

The user confirmed that example Facebook/Messenger links, hours and reply time should stay empty. Address, Instagram, YouTube and other socials are also empty. The UI therefore makes no live availability or reply-time claim. Optional hours support a tested Asia/Dhaka schedule calculation when later configured; unrecognized text displays without a false status indicator.

[Simple local and production instructions](../contact-system.md) · [Environment example](../../.env.example)

## Verification

The initial implementation was validated as below. The follow-up also verifies that missing **and blank** environment fields display the public details, and non-empty values override them. See [default-behavior checks](defaults-validation.txt), and contact pages from a server with no contact environment configuration: [desktop](screenshots/no-env-light-1280.png) / [mobile](screenshots/no-env-light-360.png).

| Check | Result |
| --- | --- |
| Django system check | Pass |
| Migration check | No changes |
| Tailwind 3.4 build | Pass |
| Palette scan | Zero extra colours; [rg evidence](palette-grep.txt) |
| Token contrast | Nine pairs pass AA; [report](palette-and-contrast.txt) |
| Contact/site tests | 20 passed |
| Affected regression suite | 78 run: 70 passed, 8 existing database-condition skips |
| Full suite | 210 run: 197 passed, 12 existing skips, 1 pre-existing migration-test error |
| Configured UI | 66 page/sheet/theme/viewport states |
| Empty fallback | 12 page/sheet/theme/viewport states |
| Browser results | **78 states**, zero HTTP errors, horizontal page overflow, measured text-contrast failures, JS errors or external resource requests |
| Keyboard and clipboard | All six width/theme modes pass focus cycling, Escape/button close, focus restoration, modal Copy feedback, clipboard success and denial |
| Order/contact forms | All eight existing order-related form bodies byte-identical; no contact form added |

The full-suite error is the existing `ReviewMigrationTests.test_duplicate_reviews_block_migration_without_deleting_data`: SQLite `NOT NULL constraint failed: accounts_user.theme_preference`. It was present before this contact work. No migration/model changes or test suppression were introduced to hide it. Automated contrast measurements supplement visual review; they are not a complete accessibility certification.

[Machine-readable summary](validation-summary.json)

## Screenshots

| Surface | Light desktop | Light mobile | Dark desktop | Dark mobile |
| --- | --- | --- | --- | --- |
| Contact page | [1280](screenshots/contact-light-1280.png) | [360](screenshots/contact-light-360.png) | [1280](screenshots/contact-dark-1280.png) | [360](screenshots/contact-dark-360.png) |
| Quick-contact sheet | [1280](screenshots/sheet-light-1280.png) | [360](screenshots/sheet-light-360.png) | [1280](screenshots/sheet-dark-1280.png) | [360](screenshots/sheet-dark-360.png) |
| My orders | [1280](screenshots/my_orders-light-1280.png) | [360](screenshots/my_orders-light-360.png) | [1280](screenshots/my_orders-dark-1280.png) | [360](screenshots/my_orders-dark-360.png) |
| Checkout | [1280](screenshots/checkout-light-1280.png) | [360](screenshots/checkout-light-360.png) | [1280](screenshots/checkout-dark-1280.png) | [360](screenshots/checkout-dark-360.png) |
| Payment | [1280](screenshots/make_payment-light-1280.png) | [360](screenshots/make_payment-light-360.png) | [1280](screenshots/make_payment-dark-1280.png) | [360](screenshots/make_payment-dark-360.png) |
| Seller dispute | [1280](screenshots/seller_dispute_response-light-1280.png) | [360](screenshots/seller_dispute_response-light-360.png) | [1280](screenshots/seller_dispute_response-dark-1280.png) | [360](screenshots/seller_dispute_response-dark-360.png) |

[Empty-configuration fallback](screenshots/contact-empty-360.png). Order screenshots use an isolated local fixture database, not production records.

## Change scope and skipped items

Python additions are presentation/configuration only: `rootline/contact.py`, context processor, environment settings, the new GET-only view/route and regression tests. Templates/CSS/JS add channels and modal/copy interactions. New reusable partials: `contact_card`, `contact_channels`, `contact_hours`, `order_contact`. Existing logo geometry and wordmark, business services, models, migrations, form bodies, view mutation logic and existing URL names/paths are preserved.

Buyer/seller order lists, order success, checkout, auction checkout, payment, raise-dispute and seller-response pages include support. Existing My orders provides the authenticated dispute flow; no new order-detail route was invented. No custom 404/500 templates existed, so those were skipped per the request. Optional channels and availability remain intentionally hidden until configured. No production service was deployed and no contact message or call was initiated.

[Changed files](changed-files.txt)
