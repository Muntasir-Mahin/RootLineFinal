# RootLine six-colour redesign: review and validation

The NexusFlow reference was studied before implementation; [DESIGN.md](../../DESIGN.md) records its actual class strings, design patterns, palette mapping and accessibility adjustments. RootLine remains a Django application with Tailwind **3.4.19**. No React, Next.js or Vite dependency was added.

The implementation covers every original **54 template**: storefront/product views; account/auth; seller tools; cart/checkout/orders/payment; auctions; disputes/reviews/wishlist; Agro Updates; search/help/chat; and the separate staff dashboard, tables, tabs, pagination and shared overlays.

## Build and check

From the repository root:

```sh
npm ci
npm run build:css
npm run check:design
python manage.py check
python manage.py makemigrations --check --dry-run
mkdir -p work
ROOTLINE_TEST_DB=work/design-tests.sqlite3 python manage.py test --noinput
```

`output.css` is regenerated and committed. `npm run watch:css` is available for local styling work. Self-hosted Geist and Geist Mono are served by Django static files; their OFL license and provenance are included in [static/fonts](../../static/fonts/README.md).

## Evidence

| Check | Result |
| --- | --- |
| Django system check | Passed, zero issues |
| Migration consistency | Passed, no changes detected |
| Original Python files | All **153** byte-identical |
| Original template tags/expressions | Preserved across all **54** templates, including order and multiplicity |
| Original form and link contracts | Zero differences across **46** rendered GET page states |
| Responsive browser audit | **276** page/theme/viewport states: 46 pages × dark/light × 360/768/1280px |
| HTTP responses | All audited pages returned 200 |
| Horizontal page overflow | Zero failures |
| Computed readable-text contrast | Zero failures against 4.5:1 normal / 3:1 large-text thresholds |
| Enabled input/focus observations | **186**, zero failures; minimum boundary 3.70:1 and focus 6.71:1 |
| Keyboard/interaction modes | Mobile/desktop × dark/light passed |
| Overlays | Cookie choices, toast, contact and confirmation dialogs passed contrast/overflow checks |
| Theme and navigation | Persistence, drawer, account/search popovers, Escape and focus return passed |
| Fonts | Both local WOFF2 requests returned 200 |
| Third-party UI requests | None on the checked interaction/screenshot pages |
| JavaScript errors | None |
| Full test suite | **197 executed: 196 passed, 1 pre-existing error** |
| Final affected account/chat/site/staff tests | **125 passed** |

The existing error is `reviews.tests.ReviewMigrationTests.test_duplicate_reviews_block_migration_without_deleting_data`: its historical user model omits `theme_preference` while the latest accounts schema remains applied, causing `NOT NULL constraint failed: accounts_user.theme_preference`. It existed before this redesign. Python was left unchanged as requested. No tests were disabled or marked expected failures.

After the full browser sweep, focused checks were repeated for the final monetary layout, compact floating controls, account controls and screenshots. Browser evidence uses an isolated fixture database; screenshot counts and prices are rendered from that database. Production application data was untouched.

The original account preview JavaScript, form methods/actions/enctypes/field names, submitter values, CSRF, upload hooks, authorization conditions, URLs and leaf SVG path remain intact. Presentation JS changes only set a dark fallback and support the responsive header popovers. Existing explicit browser/account theme preferences remain honored, including stored light preferences.

## Palette and contrast

Literal UI colours are limited to `#06141B`, `#11212D`, `#253745`, `#4A5C6A`, `#9BA8AB`, `#CCD0CF`; all other shades are derived mixes/opacity. **Additional success/error/warning colours used: none.** Monochrome labels, icons and solid/dashed/double borders convey state.

[The literal-colour scan](palette-audit.txt) has **zero** matches outside that palette across CSS, HTML, JS, MJS and SVG, including generated `output.css`. `npm run check:design` also checks encoded SVG, numeric colour functions and named colours. [The machine-readable summary](validation-summary.json) contains the executed audit counts and key contrast pairs.

| Foreground / background | Contrast |
| --- | --- |
| Dark primary: c200 / c900 | 12.01:1 |
| Dark card: c200 / c800 | 10.55:1 |
| Dark muted: c400 / c800 | 6.71:1 |
| Dark hover muted: c400 / c700 | 5.02:1 |
| Light primary: c900 / c200 | 12.01:1 |
| Light muted: c700 / c200 | 7.88:1 |
| Dark input boundary: 40% c400 + 60% c600 / c800 | 3.70:1 |

Two requested combinations needed accessibility adjustments: c600 as a headline gradient endpoint fails large-text AA (2.70:1 on c900), so readable gradients end at c400; decorative glow still uses c600. Input boundaries use the listed palette mix rather than decorative c700 so enabled controls reach 3:1. Focus, keyboard access, selection and reduced motion are preserved; the light theme inverts semantic tokens rather than adding white.

## Before / after screenshots

Each image is a real browser capture with the same isolated test data. The baseline is the untouched uploaded RootLine target. “Home” is the marketplace because the existing `/` view redirects to login/profile. Full-size 768px captures and detailed raw audits remain in the local validation workspace; the requested mobile and desktop comparisons are committed here.

| Page | Before 360px | After dark 360px | After light 360px | Before 1280px | After dark 1280px | After light 1280px |
| --- | --- | --- | --- | --- | --- | --- |
| Marketplace | [View](screenshots/before-home-360.png) | [View](screenshots/after-dark-home-360.png) | [View](screenshots/after-light-home-360.png) | [View](screenshots/before-home-1280.png) | [View](screenshots/after-dark-home-1280.png) | [View](screenshots/after-light-home-1280.png) |
| Product | [View](screenshots/before-product-360.png) | [View](screenshots/after-dark-product-360.png) | [View](screenshots/after-light-product-360.png) | [View](screenshots/before-product-1280.png) | [View](screenshots/after-dark-product-1280.png) | [View](screenshots/after-light-product-1280.png) |
| Checkout | [View](screenshots/before-checkout-360.png) | [View](screenshots/after-dark-checkout-360.png) | [View](screenshots/after-light-checkout-360.png) | [View](screenshots/before-checkout-1280.png) | [View](screenshots/after-dark-checkout-1280.png) | [View](screenshots/after-light-checkout-1280.png) |
| Chatbot | [View](screenshots/before-chatbot-360.png) | [View](screenshots/after-dark-chatbot-360.png) | [View](screenshots/after-light-chatbot-360.png) | [View](screenshots/before-chatbot-1280.png) | [View](screenshots/after-dark-chatbot-1280.png) | [View](screenshots/after-light-chatbot-1280.png) |

## Deliberate scope choices

- No page group was skipped. Shared parent templates/components also restyle the inherited views.
- Reference branding, developer/SaaS text, fake statistics, testimonial claims and pricing content were excluded.
- Statistics use existing database context only. No backend query or model was added to manufacture metrics.
- The original root redirect, account preferences, payment/order behavior, local voice/AI setup and YouTube content behavior remain unchanged. Real model inference was not part of this presentation task.
- The pre-existing Python migration-test defect is reported above rather than changing prohibited backend files.
- Font tooling is not a runtime framework dependency; only licensed WOFF2 assets were retained.

## Changed files

- `DESIGN.md`
- `accounts/templates/accounts/change_password.html`
- `accounts/templates/accounts/edit_profile.html`
- `accounts/templates/accounts/login.html`
- `accounts/templates/accounts/logout.html`
- `accounts/templates/accounts/profile.html`
- `accounts/templates/accounts/register.html`
- `accounts/templates/accounts/seller_dashboard.html`
- `agro_updates/static/agro_updates/agro.css`
- `agro_updates/templates/agro_updates/card.html`
- `agro_updates/templates/agro_updates/detail.html`
- `agro_updates/templates/agro_updates/index.html`
- `bidding/templates/bidding/auction_detail.html`
- `bidding/templates/bidding/auction_list.html`
- `bidding/templates/bidding/create_auction.html`
- `bidding/templates/bidding/edit_auction.html`
- `bidding/templates/bidding/winner_checkout.html`
- `chatbot/static/chatbot/chat.css`
- `chatbot/templates/chatbot/chat.html`
- `dashboard/static/dashboard/dashboard.css`
- `dashboard/templates/dashboard/agro_video_form.html`
- `dashboard/templates/dashboard/agro_videos.html`
- `dashboard/templates/dashboard/audit_table.html`
- `dashboard/templates/dashboard/base.html`
- `dashboard/templates/dashboard/disputes.html`
- `dashboard/templates/dashboard/orders.html`
- `dashboard/templates/dashboard/payments.html`
- `dashboard/templates/dashboard/products.html`
- `dashboard/templates/dashboard/sellers.html`
- `disputes/templates/disputes/raise_dispute.html`
- `disputes/templates/disputes/seller_response.html`
- `docs/design-review/README.md`
- `docs/design-review/palette-audit.txt`
- `docs/design-review/screenshots/after-dark-chatbot-1280.png`
- `docs/design-review/screenshots/after-dark-chatbot-360.png`
- `docs/design-review/screenshots/after-dark-checkout-1280.png`
- `docs/design-review/screenshots/after-dark-checkout-360.png`
- `docs/design-review/screenshots/after-dark-home-1280.png`
- `docs/design-review/screenshots/after-dark-home-360.png`
- `docs/design-review/screenshots/after-dark-product-1280.png`
- `docs/design-review/screenshots/after-dark-product-360.png`
- `docs/design-review/screenshots/after-light-chatbot-1280.png`
- `docs/design-review/screenshots/after-light-chatbot-360.png`
- `docs/design-review/screenshots/after-light-checkout-1280.png`
- `docs/design-review/screenshots/after-light-checkout-360.png`
- `docs/design-review/screenshots/after-light-home-1280.png`
- `docs/design-review/screenshots/after-light-home-360.png`
- `docs/design-review/screenshots/after-light-product-1280.png`
- `docs/design-review/screenshots/after-light-product-360.png`
- `docs/design-review/screenshots/before-chatbot-1280.png`
- `docs/design-review/screenshots/before-chatbot-360.png`
- `docs/design-review/screenshots/before-checkout-1280.png`
- `docs/design-review/screenshots/before-checkout-360.png`
- `docs/design-review/screenshots/before-home-1280.png`
- `docs/design-review/screenshots/before-home-360.png`
- `docs/design-review/screenshots/before-product-1280.png`
- `docs/design-review/screenshots/before-product-360.png`
- `docs/design-review/validation-summary.json`
- `orders/templates/orders/cart.html`
- `orders/templates/orders/checkout.html`
- `orders/templates/orders/my_orders.html`
- `orders/templates/orders/order_success.html`
- `orders/templates/orders/seller_orders.html`
- `package.json`
- `payments/templates/payments/make_payment.html`
- `products/templates/products/add_product.html`
- `products/templates/products/delete_product.html`
- `products/templates/products/edit_product.html`
- `products/templates/products/marketplace.html`
- `products/templates/products/marketplace_product_detail.html`
- `products/templates/products/my_products.html`
- `products/templates/products/product_detail.html`
- `reviews/templates/reviews/add_review.html`
- `reviews/templates/reviews/seller_reviews.html`
- `scripts/check_design.mjs`
- `static/css/output.css`
- `static/css/site-tools.css`
- `static/css/theme.css`
- `static/favicon.svg`
- `static/fonts/OFL.txt`
- `static/fonts/README.md`
- `static/fonts/geist-mono.woff2`
- `static/fonts/geist-sans.woff2`
- `static/js/site-tools.js`
- `static/js/theme-init.js`
- `tailwind.config.js`
- `templates/base.html`
- `templates/components/badge.html`
- `templates/components/button.html`
- `templates/components/card.html`
- `templates/components/faq_item.html`
- `templates/components/footer_links.html`
- `templates/components/page_header.html`
- `templates/components/section_heading.html`
- `templates/components/stat.html`
- `templates/site/help.html`
- `templates/site/search.html`
- `wishlist/templates/wishlist/my_wishlist.html`
