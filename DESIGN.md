# RootLine marketplace design — stages 1 and 2

## Scope and review gate

Stage 1 audits the existing application and establishes the design. Stage 2 implements the shared foundation, header, footer, mobile tabs and reusable product card, demonstrated in the existing product grid. Stages 3–7 are pending the user's OK. Existing page compositions remain until those stages; this is not the finished marketplace home.

## Audit

The application has 54 page/layout/partial templates plus shared components (inventory below). Public catalogue, seller CRUD, orders/cart/checkout, payment, auctions, reviews, disputes, wishlist, account/auth, staff dashboard, chatbot and Agro Updates use their existing URL names. Root `/` redirects to login/profile; Marketplace is `/products/`. No URL changes are needed.

`Product` has one optional image, category (free text), stock, unit, fixed/bidding/both and pending/verified/rejected states. There is no gallery or featured flag. Ratings come from reviews; seller identity is the username. Existing cart mutations accept POST quantity and retain their purchase validation. Auction purchases can be blocked by settlement rules. Product-card actions use those existing endpoints; auction/both cards route to details before purchase when auction settlement can matter.

Marketplace view already restricts products to verified, available, positive stock. Its search/category/price/type/sort filters are real; categories in the old template were hard-coded. It has no pagination. Site search groups public products/published videos and already paginates; no category filter exists. Stage 2 adds a bounded category filter to this read-only query. Later UI must explain the marketplace's verified/in-stock constraint instead of promising unavailable records.

Before: theme.css owns dark-first tokens, Geist Sans/Mono and dense uppercase labels. site-tools.css owns a narrow popover search, hidden cart, navigation, overlays and footer. chat.css, agro.css and dashboard.css consume the same semantic variables but use small mono labels. Tailwind output.css is generated with 3.4; utility colours reference tokens. There are no green utility overrides to retain. The page hero uses a decorative grid/glow and headings run oversized. Cards use placeholders unless a seller uploads a photo. No real product photos are available in the supplied archive; no demo photos or products will be inserted into production data.

## Foundation

Light is the fallback; account/local saved preferences remain authoritative. Header and footer use the light card surface with a subtle palette border; dark mode uses c800 cards. Logo paths and wordmark remain unchanged, recoloured by tokens.

Palette: c900 #06141B, c800 #11212D, c700 #253745, c600 #4A5C6A, c400 #9BA8AB, c200 #CCD0CF. White is used only inside color-mix to make the permitted light tints. No additional status colours. Validation also uses text/icons/dashed borders so meaning does not depend on colour.

Light page = 18% c200 + white; card = 4% c200 + white; hover = 32% c200 + white. Primary c700, hover c800, text c900, secondary c600, control border c600, focus c700. Dark page c900, card c800, hover c700, border c700, text c200, secondary c400, focus c400. Dark control border c400/c600 mix provides 3:1. Decorative borders do not identify inputs.

One readable Geist sans family plus self-hosted Noto Sans Bengali fallback (400/600/700). Body 16px, line height 1.6. Scale: supporting 14px, body/buttons/nav 16px, card headings 18px, section 24–32px, page 32–40px. Mono only for prices/quantities/order IDs and tiny badges. Controls >=44px, radius 8px; cards radius 12px; one soft shadow. Spacing multiples of 4/8. No grid/glow or page edge rails. Existing page selectors remain temporarily for layout compatibility; the foundation is edited in place rather than stacked overrides.

## Components and patterns

Product card: 4:3 lazy image or leaf placeholder, linked image/title with stretched card link, seller, price/unit, real rating when available, verified and selling type, stock, POST wishlist and existing cart action. Own items show Manage; bidding/both items show View auction/details to preserve auction rules. No nested anchors/forms. Leaf placeholder is expected where sellers have not supplied images.

Header: logo, large always-visible desktop search with real category filter, visible cart count (distinct product lines, not summed fractional kilograms), wishlist, account menu and icon theme control. Categories come from eligible public products with real counts. Seller links depend on seller_approved; staff entry depends on is_staff. Mobile search is expanded from its icon or bottom Search tab; hamburger exposes all navigation; fixed bottom tabs expose Home/Search/Cart/Orders/Account and aria-current.

Footer: Shop/Sell/Support/Company columns with existing destinations only; seller links gated. Cookie preferences and contact stay functional. Skip link, confirmations, toast, UTM consent, focus and reduced motion retained. Shared components are extended as pages reach their stage.

## Python changes allowed in stage 2

- rootline/context_processors.py: add read-only marketplace_navigation, with public category/count query and authenticated cart-line count; never get_or_create.
- rootline/settings.py: register that processor.
- rootline/site_views.py: read-only category constraint for existing public product search, including category-only requests; videos retain existing query semantics. No business mutation, model, migration, form or route changes.
- rootline/test_site.py: regression tests for visibility, counts, permissions and search isolation.

## Later stages / constraints

3: compact marketplace hero, real category tiles, list pagination/filter chips, real live auctions/updates, product detail and related products. No fake statistics or unsupported gallery.
4: cart/details/payment/done progress, order summaries/status timelines.
5: account sidebar/overview, seller/staff tables, disputes/reviews/wishlist.
6: auctions, chat, updates, help, grouped search and auth page compositions.
7: remove obsolete selectors, full regression suite and desktop/mobile before/after report.

The existing full suite has one baseline ReviewMigrationTests schema error (`accounts_user.theme_preference` NOT NULL), documented in docs/design-review. This is outside the permitted model/migration scope; do not call the full suite passing unless resolved within authorization.

## Template inventory (existing paths)

Each uses shared theme.css and output.css via base.html, except staff pages which extend dashboard/base.html and load dashboard.css. Chat additionally loads chatbot/chat.css, Agro Updates loads agro_updates/agro.css. Components inherit their parent's styles. The following original inventory is retained:

- `accounts/templates/accounts/change_password.html`
- `accounts/templates/accounts/edit_profile.html`
- `accounts/templates/accounts/login.html`
- `accounts/templates/accounts/logout.html`
- `accounts/templates/accounts/profile.html`
- `accounts/templates/accounts/register.html`
- `accounts/templates/accounts/seller_dashboard.html`
- `agro_updates/templates/agro_updates/card.html`
- `agro_updates/templates/agro_updates/detail.html`
- `agro_updates/templates/agro_updates/index.html`
- `bidding/templates/bidding/auction_detail.html`
- `bidding/templates/bidding/auction_list.html`
- `bidding/templates/bidding/create_auction.html`
- `bidding/templates/bidding/edit_auction.html`
- `bidding/templates/bidding/winner_checkout.html`
- `chatbot/templates/chatbot/chat.html`
- `dashboard/templates/dashboard/activity.html`
- `dashboard/templates/dashboard/agro_video_form.html`
- `dashboard/templates/dashboard/agro_videos.html`
- `dashboard/templates/dashboard/audit_table.html`
- `dashboard/templates/dashboard/base.html`
- `dashboard/templates/dashboard/dispute_detail.html`
- `dashboard/templates/dashboard/disputes.html`
- `dashboard/templates/dashboard/orders.html`
- `dashboard/templates/dashboard/overview.html`
- `dashboard/templates/dashboard/pagination.html`
- `dashboard/templates/dashboard/payments.html`
- `dashboard/templates/dashboard/products.html`
- `dashboard/templates/dashboard/sellers.html`
- `dashboard/templates/dashboard/tabs.html`
- `disputes/templates/disputes/raise_dispute.html`
- `disputes/templates/disputes/seller_response.html`
- `orders/templates/orders/cart.html`
- `orders/templates/orders/checkout.html`
- `orders/templates/orders/my_orders.html`
- `orders/templates/orders/order_success.html`
- `orders/templates/orders/seller_orders.html`
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
- `templates/base.html`
- `templates/components/badge.html`
- `templates/components/button.html`
- `templates/components/card.html`
- `templates/components/faq_item.html`
- `templates/components/footer_links.html`
- `templates/components/form_fields.html`
- `templates/components/icon.html`
- `templates/components/page_header.html`
- `templates/components/page_heading.html`
- `templates/components/section_heading.html`
- `templates/components/stat.html`
- `templates/site/help.html`
- `templates/site/search.html`
- `wishlist/templates/wishlist/my_wishlist.html`


## Agro identity extension — October 2026

The approved visual identity task supersedes the earlier six-colour-only rule
for brand accents. Existing neutrals, Geist/Noto Sans Bengali, navigation,
features, routes, and radius scale remain. This is a visual-only update, not
implementation of the older deferred backend/page redesign stages.

| Role | Light | Dark |
| --- | --- | --- |
| Leaf / primary | `#245B3D` | `#9DCE9B` |
| Primary hover | `#19432C` | `#B8D99A` |
| Fresh greenery | `#B8D99A` | `#395D3D` |
| Soil | `#78563B` | `#C8A27B` |
| Harvest | `#D8AE48` | `#E6C568` |
| Cream / illustrated fabric | `#F7F4EA` | `#ECF1E8` |
| Page | `#F7F4EA` | `#122019` |
| Card | `#FDFCF7` | `#192B21` |
| Soft tint | `#EDF2E5` | `#243B2C` |
| Decorative border | `#CFD9C8` | `#3C5744` |

Skin (`#B87D52`) and produce clay (`#A6533F`) are artwork-only tones; neither
is a status colour or body-text colour. Body text/muted text keep the shared
neutral tokens. Harvest/fresh accents are decorative, never low-contrast labels.
Controls stay 8px, cards 12px, profile avatars round. No new heading font is
loaded. Headings keep the readable sans treatment and gain a small leaf accent.

### Reusable original illustration gallery

Open [`/static/illustrations/agro/gallery.html`](static/illustrations/agro/gallery.html)
while the development server runs to see every asset in light and dark palettes.
The files are in `static/illustrations/agro/`; each is below 3 KB.

| Growers | Plants | Helpers |
| --- | --- | --- |
| [Basket grower](static/illustrations/agro/farmer-basket.svg) | [Leaf](static/illustrations/agro/leaf.svg), [sprout](static/illustrations/agro/sprout.svg) | [Corner](static/illustrations/agro/corner.svg) |
| [Paddy grower](static/illustrations/agro/farmer-paddy.svg) | [Paddy](static/illustrations/agro/paddy.svg), [tomato](static/illustrations/agro/tomato.svg) | [Field divider](static/illustrations/agro/field-divider.svg) |
| [Woman grower](static/illustrations/agro/farmer-woman.svg) | [Tree](static/illustrations/agro/tree.svg), [vine](static/illustrations/agro/vine.svg) | [Horizon](static/illustrations/agro/field-horizon.svg), [blob](static/illustrations/agro/organic-blob.svg) |

Include `components/agro_illustration.html` with the asset's `art` name. For
plant assets pass width/height `180`; for the divider pass `1200`/`64`, and
horizon `1200`/`120`. Default farmer/blob dimensions are `480`/`360`. A same-origin
SVG `<use>` reuses each small cacheable file while inheriting theme variables.
Decorative SVGs are hidden from assistive technology and contain no image text.
The art is static, has reserved dimensions, and adds no animation or library.
Below-fold horizon/divider SVGs use native lazy-loaded images with small dark
variants (`field-horizon-dark.svg`, `field-divider-dark.svg`). Set `lazy=True`
only for those two art names. Other art uses cacheable vector references;
real below-fold photos retain/add native lazy loading. Keep only one full scene
in a content-heavy viewport; small heading leaves/dividers are decoration.

Validation: `npm run check:design` checks the extended allowlist plus real agro
text/button AA pairs. `npm run build:css` builds shared Tailwind; Partner utilities
use `npx tailwindcss -c partners/tailwind.config.js -i partners/static/partners/source.css -o partners/static/partners/partners.css --minify`.
