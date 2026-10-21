# Marketplace-first: stage 2 review

Stages 1 and 2 are implemented on `feature/rootline-marketplace-first`. **Stages 3–7 await your OK**, as requested. This is a foundation review, not the completed marketplace home. The old page compositions remain for their scheduled stages; the product-card component is demonstrated in the existing marketplace grid.

## What changed

- Audit, page inventory, tokens, type scale, component plan and constraints: [DESIGN.md](../../DESIGN.md).
- Light default with saved account/local preferences retained. Light-tinted header/footer, dark palette surfaces in dark mode. Original RootLine leaf path and wordmark retained.
- Large desktop search plus real category selection, visible cart with count of product lines, wishlist, account menu, seller/staff entries gated by the original user fields. Top categories/counts reflect eligible public products, not hard-coded categories.
- Mobile search/drawer, bottom Home/Search/Cart/Orders/Account tabs and active state; Escape returns focus. Icon theme control preserves server preference saving.
- Four footer columns: Shop, Sell, Support, Company. Existing cookie preferences, help/contact, toast, confirmation, skip link and campaign consent retained.
- Reusable product card: lazy 4:3 image, leaf fallback, seller, price/unit, real rating when present, verified/selling-type badges, stock, wishlist POST and Add to cart POST. Auction/both listings route to their original detail purchase checks; sellers see Manage for their own product. Existing purchase endpoints retain all validation.
- Geist sans for normal text; local Noto Sans Bengali 400/600/700 for Bangla; mono retained for transactional amounts/identifiers. No external font service or new runtime dependency. Shared chat/Agro/staff CSS typography follows the foundation; their page compositions await later stages.
- Removed decorative grid/glow and page rails, retained compatible layout selectors until their pages are redesigned. Fixed hidden controls being made visible by component display rules. No `!important` added.

## Python additions (read-only)

| File | Reason |
| --- | --- |
| `rootline/context_processors.py` | Public category counts and signed-in cart-line count. No cart creation or writes. |
| `rootline/settings.py` | Register that context processor. |
| `rootline/site_views.py` | Add a bounded category constraint to existing public product search, including category-only search. Video query semantics unchanged. |
| `rootline/test_site.py` | Regression tests for public visibility, user-scoped cart counts, no cart creation, seller/staff entry gating and category search. |

No models, migrations, forms, business mutations or URLs changed. No real data seeded or altered; browser fixtures use an isolated disposable database outside the repository.

## Checks

- `python manage.py check`: passes; `makemigrations --check --dry-run`: no changes.
- `npm run build:css`: passes using Tailwind 3.4.19; output regenerated (no utility changes, so its bytes remain the same).
- `npm run check:design`: zero palette violations, all nine text token pairs AA. White only inside the permitted light mixes; **additional status colours: none**. [Report](contrast-and-palette.txt), [rg scan](palette-grep.txt).
- Light muted text: 6.43:1 on page, 6.82:1 on cards, 6.06:1 on hover tint. Light button text: 7.88:1. Dark secondary on cards: 6.71:1, dark hover: 5.02:1.
- 46 pages × two themes × 360/768/1280 = **276 browser states**, zero HTTP errors, horizontal page overflow or measured text-contrast failures. Automated contrast checks supplement visual review; they are not a complete accessibility certification.
- Final before/after captures of marketplace, product, cart, account and chatbot. After captures cover both themes at all three widths. The demo database has no uploaded product photos, so screenshots deliberately show the supported fallback.
- Keyboard drawer/search/Escape, category search, guest light fallback, persisted dark preference, 44px navigation/card/footer targets, and JavaScript error checks pass at all three widths. [Interaction results](interactions.json).
- Targeted Django tests: **68 run, 60 pass, 8 existing database-condition skips**.
- Full suite: **200 run, 187 pass, 12 existing skips, 1 pre-existing error**: `reviews.tests.ReviewMigrationTests.test_duplicate_reviews_block_migration_without_deleting_data`, SQLite `NOT NULL constraint failed: accounts_user.theme_preference`. This is the historical-model/schema error already recorded in the previous design review. It is not hidden, disabled or fixed through an unauthorized migration change.

## Stage 2 previews

| Preview | Desktop | Mobile |
| --- | --- | --- |
| Shared header / existing home | [1280px](screenshots/header-light-1280.png) | [360px](screenshots/header-light-360.png) |
| Product card component | [1280px](screenshots/cards-light-1280.png) | [360px](screenshots/cards-light-360.png) |
| Mobile drawer | — | [360px](screenshots/drawer-360.png) |

Full-page comparisons below reflect stage 2 foundation changes; the later page-specific redesigns are pending.

| Page | Before desktop/mobile | Stage 2 light desktop/mobile | Stage 2 dark desktop/mobile |
| --- | --- | --- | --- |
| Marketplace | [1280](screenshots/before-home-1280.png) / [360](screenshots/before-home-360.png) | [1280](screenshots/stage2-light-home-1280.png) / [360](screenshots/stage2-light-home-360.png) | [1280](screenshots/stage2-dark-home-1280.png) / [360](screenshots/stage2-dark-home-360.png) |
| Product | [1280](screenshots/before-product-1280.png) / [360](screenshots/before-product-360.png) | [1280](screenshots/stage2-light-product-1280.png) / [360](screenshots/stage2-light-product-360.png) | [1280](screenshots/stage2-dark-product-1280.png) / [360](screenshots/stage2-dark-product-360.png) |
| Cart | [1280](screenshots/before-cart-1280.png) / [360](screenshots/before-cart-360.png) | [1280](screenshots/stage2-light-cart-1280.png) / [360](screenshots/stage2-light-cart-360.png) | [1280](screenshots/stage2-dark-cart-1280.png) / [360](screenshots/stage2-dark-cart-360.png) |
| Account | [1280](screenshots/before-account-1280.png) / [360](screenshots/before-account-360.png) | [1280](screenshots/stage2-light-account-1280.png) / [360](screenshots/stage2-light-account-360.png) | [1280](screenshots/stage2-dark-account-1280.png) / [360](screenshots/stage2-dark-account-360.png) |
| Chatbot | [1280](screenshots/before-chatbot-1280.png) / [360](screenshots/before-chatbot-360.png) | [1280](screenshots/stage2-light-chatbot-1280.png) / [360](screenshots/stage2-light-chatbot-360.png) | [1280](screenshots/stage2-dark-chatbot-1280.png) / [360](screenshots/stage2-dark-chatbot-360.png) |

## Pending review

Stages 3–7 include marketplace composition/category tiles/filter chips/pagination, product detail, purchase flows, account sidebar/dashboard pages, auctions/chat/editorial/auth composition, remaining component consolidation and final cleanup/QA. No language switch. No sample statistics, reviews, photos or products added to production. The models supply one product image, not an image gallery. Availability/verification filters cannot expose records excluded by existing business rules.

After stage 2 approval, proceed to stage 3. Changed paths are in [changed-files.txt](changed-files.txt). The previous six-colour design remains documented separately under `docs/design-review/`.
