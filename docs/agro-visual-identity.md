# RootLine agro visual identity

Branch: `feature/agro-visual-identity`, based on `feature/registration-camera-photo`
at `59ba8e2`. No branches were merged. The camera feature and earlier Partner /
seller work remain available through that ancestry. Work was split into shared
assets/tokens, then application to existing templates.

Only visual assets, CSS/Tailwind tokens, template presentation, the design check,
and documentation changed. No Python, database models, migrations, business
services, views, URLs, settings, or existing JavaScript logic changed. Form
field names, CSRF, destinations and account/Partner conditions remain intact.

## Preview locally

1. Use the existing virtual environment and `.env`. No new package, secret or
   migration is required for this visual upgrade.
2. If CSS must be regenerated, run these exact commands from beside `manage.py`:

   ```sh
   npm ci
   npm run build:css
   npx tailwindcss -c partners/tailwind.config.js -i partners/static/partners/source.css -o partners/static/partners/partners.css --minify
   ```

   Both builds were run. The generated CSS was unchanged because the page changes
   reuse existing utilities and the new palette is provided by CSS variables.
3. Run `python manage.py runserver`, then hard refresh with **Cmd + Shift + R**.
4. Visit the pages below on a wide screen, 768px tablet and 360px mobile. Use the
   existing moon/theme button for dark mode. The art/form split is desktop-only;
   compact forms remain the priority on smaller screens.
5. For deployment, use the project's usual `python manage.py collectstatic --noinput`.
   SVG `<use>` references must be served from the same origin as the page. The
   supplied SVG files have MIME type `image/svg+xml`; preserve that on deployment.

| Page / state | Path and how to preview |
| --- | --- |
| Marketplace/home hero | `/products/`; `/` keeps its existing login/profile redirect |
| Marketplace empty state | `/products/?search=a-name-that-does-not-exist` |
| My account / Partner shortcut | `/profile/` after login; check a customer, pending Partner, approved Partner, and staff account |
| Login / registration | `/login/`, `/register/`; verify Choose File and Take photo still work |
| Password recovery | `/password/reset/`, `/password/reset/sent/`, `/password/reset/complete/`; follow a genuine reset link to preview the new-password form |
| Username recovery | `/username/recover/`, `/username/recover/sent/` |
| Agro Partners directory | `/partners/`; `/partners/?q=a-company-that-does-not-exist` for empty state |
| Partner Store | Open an approved company from the directory: `/partners/<company-slug>/`; test with and without uploaded cover/logo |
| Agro Updates | `/agro-updates/`; try a non-matching search to check its compact empty state |
| Empty cart / orders / wishlist | `/orders/cart/`, `/orders/my-orders/`, `/wishlist/` with an account without those items |
| Search empty state | `/search/?q=a-name-that-does-not-exist` |
| Shared footer / accents | Scroll any public page; compare both themes |
| Illustration gallery | `/static/illustrations/agro/gallery.html`; shows all designs in both palettes |
| 404 | With production-like `DEBUG=False` and correct hosts/secret, open a nonexistent URL; Django's debug page remains authoritative with `DEBUG=True` |
| 500 | The built-in handler was rendered directly in an isolated check; do not deliberately trigger production failures just to preview it |

The shared palette also colours other pages that consume the existing semantic
CSS variables. Their layout, controls and features were not rewritten. The
recovery confirmation messages and email contents were not changed.

## Real photo / placeholder slots

All new artwork is original SVG. There are no stock URLs, new remote image
requests, new photo dependencies, fake product records or demo data in the app.
The plant fallbacks already work without supplying any photos. Existing uploads
continue to take precedence.

| Existing slot | Recommended source and dimensions | Where to supply it |
| --- | --- | --- |
| Partner Store cover (marked plant placeholder in template) | Your own Bangladesh farm/field or company team photo, **1600 × 400**, landscape; keep faces away from extreme edges | Partner Dashboard → Company profile → Cover image |
| Partner directory/store logo (sprout fallback when missing) | Your own company logo, **400 × 400** square | Company profile → Logo |
| Company gallery | Your own farmers, fields, facilities or produce photos, **1200 × 800** landscape; obtain people's consent | Partner Dashboard → Gallery |
| Product image (existing leaf fallback) | Your actual produce on a clean background, **800 × 600** (4:3), also test portrait and wide uploads | Existing add/edit product form |

There is no new compulsory home-photo slot: the original farmer scene is the
finished hero. A real home photo gallery is an optional future task below.

## Verification and limits

- `python manage.py check`: passed.
- `npm run check:design`: zero palette violations; **21 documented text/button
  pairs passed WCAG AA**, including 12 actual agro-theme pairs. Lowest actual
  agro text/button result is 4.94:1. Illustrations are decorative and hidden from
  assistive technology; they carry no embedded text.
- Existing full Django suite: **298 tests, 297 passed, one pre-existing error**:
  `reviews.tests.ReviewMigrationTests.test_duplicate_reviews_block_migration_without_deleting_data`,
  `IntegrityError: NOT NULL constraint failed: accounts_user.theme_preference`.
  It was already documented before this work and is outside this visual task.
- Chromium: **114 page/size/theme combinations** across 1440px, 768px, and 360px;
  no horizontal overflow or JavaScript errors. Checked account roles and Partner
  destinations, the completed shortcut grid, Bangla name layout, camera capture,
  desktop product hover controls, and decorative SVG dimensions/accessibility.
- Additional checks: valid reset form, reduced-motion hover suppression, lazy
  light/dark footer variants, and built-in Django 404/500 template rendering.
- **13 original designs / 15 SVG files**, including two tiny dark variants. Each
  is below 3 KB (well below 15 KB), XML-valid and contains no script, raster
  image, image text or external URL. Same-origin SVG references are cached;
  below-fold footer/divider images use native lazy loading and reserved sizes.
- Desktop/mobile and light/dark screenshots were inspected. Browser fixtures
  and screenshots live under ignored `work/agro-identity/`; the real database
  and uploaded media were untouched. Physical device / Safari checks remain a
  recommended deployment check; automated verification used Chromium.

## Optional next upgrades — not implemented

1. A small home gallery using your own Bangladesh farmer/field photography.
2. A seasonal crop banner with accurate local harvest information.
3. A Bangla/English language toggle with proper translated page content.

## Complete file inventory

Every path below is relative to the repository root. This lists only this
branch's visual changes after `59ba8e2`; files from the earlier camera/Partner
branches are not counted again.

| File | Reason |
| --- | --- |
| `DESIGN.md` | Document the approved agro palette extension, reusable artwork gallery, and usage rules. |
| `accounts/templates/accounts/login.html` | Replace the desktop leaf block with the paddy-grower artwork; preserve login controls. |
| `accounts/templates/accounts/password_reset_complete.html` | Add the shared desktop recovery panel around the existing form or response, hidden on small screens. |
| `accounts/templates/accounts/password_reset_confirm.html` | Add the shared desktop recovery panel around the existing form or response, hidden on small screens. |
| `accounts/templates/accounts/password_reset_done.html` | Add the shared desktop recovery panel around the existing form or response, hidden on small screens. |
| `accounts/templates/accounts/password_reset_form.html` | Add the shared desktop recovery panel around the existing form or response, hidden on small screens. |
| `accounts/templates/accounts/profile.html` | Add the named welcome banner and missing staff shortcut icon. |
| `accounts/templates/accounts/register.html` | Replace desktop decoration with the basket grower; retain upload/camera and signup fields. |
| `accounts/templates/accounts/username_recovery_done.html` | Add the shared desktop recovery panel around the existing form or response, hidden on small screens. |
| `accounts/templates/accounts/username_recovery_form.html` | Add the shared desktop recovery panel around the existing form or response, hidden on small screens. |
| `agro_updates/templates/agro_updates/index.html` | Use the paddy-grower header and add a public empty-state return action. |
| `docs/agro-visual-identity.md` | Record preview steps, photo slots, verification, limits and this complete inventory. |
| `orders/templates/orders/cart.html` | Use the original sprout in the existing empty cart state. |
| `orders/templates/orders/my_orders.html` | Add the plant, friendly empty-order heading, and existing marketplace destination. |
| `partners/templates/partners/account_link.html` | Keep all membership/link conditions and delegate the visible link content. |
| `partners/templates/partners/account_link_content.html` | Add the Partner shortcut icon, one-line description and arrow only in the profile tile. |
| `partners/templates/partners/base.html` | Expose presentation-only heading-class/art blocks for directory/store headers. |
| `partners/templates/partners/directory.html` | Add paddy heading, sprout logo fallback and empty-state art/action. |
| `partners/templates/partners/store.html` | Add paddy heading, a marked field-pattern cover fallback, and image dimensions. |
| `products/templates/products/marketplace.html` | Add the grower hero, short tagline, field divider and plant empty state. |
| `scripts/check_design.mjs` | Extend the palette allowlist and test actual light/dark agro AA text/button pairs. |
| `static/css/agro-identity.css` | Style responsive artwork, headers, lazy theme variants, and odd final shortcut row. |
| `static/css/theme.css` | Extend tokens with agro colours and matching light/dark semantic surfaces/controls. |
| `static/illustrations/agro/corner.svg` | Create original leaf corner decoration artwork. |
| `static/illustrations/agro/farmer-basket.svg` | Create original Bangladeshi grower in a woven sun hat with a vegetable basket artwork. |
| `static/illustrations/agro/farmer-paddy.svg` | Create original grower standing with paddy and a small rice sheaf artwork. |
| `static/illustrations/agro/farmer-woman.svg` | Create original woman grower with draped scarf and produce artwork. |
| `static/illustrations/agro/field-divider-dark.svg` | Provide the small dark variant for native lazy-loaded field divider. |
| `static/illustrations/agro/field-divider.svg` | Create original subtle wavy field-line divider artwork. |
| `static/illustrations/agro/field-horizon-dark.svg` | Provide the small dark variant for native lazy-loaded field horizon. |
| `static/illustrations/agro/field-horizon.svg` | Create original layered field horizon artwork. |
| `static/illustrations/agro/gallery.html` | Show all 13 artwork designs with captions in both palettes, without a Django route. |
| `static/illustrations/agro/leaf.svg` | Create original leaf motif artwork. |
| `static/illustrations/agro/organic-blob.svg` | Create original soft organic background silhouette artwork. |
| `static/illustrations/agro/paddy.svg` | Create original paddy stalk artwork. |
| `static/illustrations/agro/sprout.svg` | Create original seedling artwork. |
| `static/illustrations/agro/tomato.svg` | Create original tomato plant artwork. |
| `static/illustrations/agro/tree.svg` | Create original tree artwork. |
| `static/illustrations/agro/vine.svg` | Create original vine artwork. |
| `tailwind.config.js` | Expose the agro palette as Tailwind token-backed utility colours. |
| `templates/404.html` | Supply the built-in Django 404 handler with a friendly illustrated page. |
| `templates/500.html` | Supply the built-in Django 500 handler with a friendly illustrated page. |
| `templates/base.html` | Load the visual stylesheet and lazy footer horizon; update the short brand line. |
| `templates/components/agro_auth_story.html` | Reuse the recovery illustration panel without changing any recovery messages. |
| `templates/components/agro_empty_art.html` | Reuse a small decorative sprout in empty states. |
| `templates/components/agro_illustration.html` | Render same-origin theme-aware SVG references and lazy footer/divider variants. |
| `templates/site/search.html` | Add a single small plant and marketplace link to the product empty state. |
| `wishlist/templates/wishlist/my_wishlist.html` | Add the plant and existing marketplace destination to the empty wishlist. |
