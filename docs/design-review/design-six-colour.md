# RootLine design language

## Reference study completed before implementation

Studied `nexusflow-react-personal/src/index.css` and Header, Hero, TerminalPreview, LogoCloud, Features, FeatureCard, Solutions, Stats, StatCard, Testimonials, Pricing, PricingCard, Faq, FaqItem, CTA, Footer and FooterLinkColumn. The attached RootLine source matches the existing checkout byte for byte. Keep Django, Tailwind 3.4 and all existing backend contracts.

This ports structure, spacing, hierarchy and interaction styling. RootLine keeps its leaf logo, product data, farming language, real prices, existing forms and links. Reference branding, marketing claims, artificial metrics, testimonials and deployment content are excluded.

## Exact reference patterns and RootLine translations

| Pattern | Actual reference classes | RootLine treatment |
| --- | --- | --- |
| Header | `sticky top-0 z-50 w-full border-b border-[#1f1f1f] bg-black/80 backdrop-blur-md transition-all`; inner `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`, `h-16` | One 64px brand/action row, existing leaf and wordmark, mono ORGANIC MARKETPLACE pill; navigation/search drawer retains every existing route and ID. All links collapse below the width where they can fit without clipping. |
| Hero | `relative pt-16 pb-20 md:pt-24 md:pb-28 overflow-hidden vercel-glow`; `text-center max-w-4xl mx-auto mt-8 space-y-5` | Farming headline, centered command-style product search, 40px grid and top glow. No fake user counts or testimonials. |
| Hero title | `text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.08]`; `bg-gradient-to-b from-white via-neutral-200 to-neutral-500 bg-clip-text text-transparent` | Geist 36px through 72px, bold and tight. Readable gradient uses c200 to c400; requested c600 endpoint is reserved for nontext decoration because it fails even large-text AA on c900 (2.70:1). |
| Command box | `flex items-center justify-between gap-3 px-3.5 py-2.5 bg-[#0a0a0a] border border-neutral-800 rounded-lg text-xs font-mono` | Existing marketplace search and filter fields, preserved names and GET submission. |
| Section | `py-24 border-b border-neutral-800`; `text-left max-w-2xl space-y-2 mb-16` | Desktop 96px section rhythm, smaller mobile spacing, left-aligned heading and real RootLine context. |
| Eyebrow | `text-xs font-mono text-neutral-400 uppercase tracking-widest` | `[ 01 ] FRESH PRODUCE`, `[ 02 ] GROW WITH ROOTLINE` and meaningful page labels. |
| Feature grid | `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-neutral-800 border border-neutral-800 rounded-xl overflow-hidden` | Category/workflow and account shortcut grid: 1px divided structure, semantic surface tokens. |
| Feature card | `p-8 bg-[#0a0a0a] hover:bg-[#111111] transition-colors group`; icon `w-10 h-10 rounded-lg ... border ... mb-6` | Rounded/bordered product and workflow cards, quiet hover surface changes, existing RootLine icons. |
| Solutions | `grid grid-cols-1 lg:grid-cols-12 gap-12 items-center`, `space-y-28` | Balanced product/detail and profile layouts with mobile stacking, no imported reference diagrams. |
| Stats | `text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight font-mono`; label `text-xs font-mono uppercase tracking-wider` | Real existing seller/dashboard counts and order totals only. No invented marketplace statistics. |
| Pricing panel | `p-8 rounded-xl bg-[#0a0a0a] flex flex-col justify-between space-y-6`; featured `border-2 border-white relative` | Checkout/order summary, product purchase and active auction panels, 2px foreground border and literal status badge where state is known. |
| Primary button | `inline-flex items-center justify-center gap-2 px-5 py-2.5 text-xs font-medium rounded-lg transition-colors font-mono whitespace-nowrap` | Foreground surface, page-colour text; mono labels, 44px minimum touch target, no text wrapping outside bounds. |
| Secondary button | `text-neutral-300 bg-neutral-900 hover:bg-neutral-800 ... border border-neutral-800` | Surface background and visible border; labels preserve original actions. |
| Terminal frame | `rounded-xl border border-neutral-800 bg-[#0a0a0a] shadow-2xl overflow-hidden font-mono`; bar `flex flex-wrap ... px-4 py-3 border-b ... text-xs` | Chat workspace with mono top bar, real connection/voice status and existing message/composer controls. |
| FAQ | `divide-y divide-neutral-800 border-y border-neutral-800`; rows `py-6 px-3`; question `flex ... justify-between gap-4 text-left` | Native accessible details/summary and existing help answers, reusable faq_item component. |
| CTA | `rounded-2xl border border-neutral-800 ... p-8 sm:p-16 text-center ... relative overflow-hidden` | Shop / seller / help calls to action with real routes and RootLine copy. |
| Footer | `border-t ... text-xs`; columns `grid grid-cols-2 md:grid-cols-5 gap-8`, mono `text-[11px] ... uppercase tracking-wider` | Brand plus three useful RootLine link columns (four columns total), existing account conditions, cookies and support. No fake operational status. |
| Detail | `::selection`, 6px scrollbar, rounded 3px thumb, transition-colors | Palette-only selection, thin scrollbar, visible keyboard focus, reduced-motion support. |

## Palette mapping

Only these six literal colours are permitted in authored or generated presentation code. Transparent layers and tints are derived using `color-mix` or opacity. No additional status hues are introduced: status meaning is conveyed by text, icons, weight and border styles.

| Token | Value | Dark role | Light role |
| --- | --- | --- | --- |
| `--c-900` | `#06141B` | Page, primary-button text | Primary text, primary button |
| `--c-800` | `#11212D` | Section/card surface, secondary button | Strong text on pale surfaces |
| `--c-700` | `#253745` | Hover surfaces, borders | Muted readable text, hover button |
| `--c-600` | `#4A5C6A` | Hover borders, grid/glow decoration | Borders, focus decoration (never body text) |
| `--c-400` | `#9BA8AB` | Muted readable text, primary hover/focus | Surface decoration only; never text on pale surfaces |
| `--c-200` | `#CCD0CF` | Primary text, primary button | Page/card surface, primary-button text |

Semantic variables (`--page`, `--surface`, `--surface-hover`, `--border`, `--border-hover`, `--text`, `--muted`, `--primary`, `--on-primary`, `--focus`) centralize themes. Light surfaces can use c200/c400 mixes, with c900 primary and c700 secondary text. No white or black additions.

Verified baseline contrast: c200/c900 12.01:1; c200/c800 10.55:1; c400/c800 6.71:1; c400/c700 5.02:1; c700/c200 7.88:1. Prohibited body pairs include c600/c800 (2.37), c600/c200 (4.45), c400/c200 (1.57). Essential input boundaries use a c400/c600 mix (40%/60%, about 3.70:1 on c800) instead of decorative c700 borders, which would fail nontext contrast. Light inputs use c600 borders. Full computed report follows implementation.

Dark is the fallback for visitors with no saved preference; existing explicit browser/account preferences remain honored, including stored light account preferences. No Python model defaults change.

## Technical plan and invariants

1. Design study/document and mapping first.
2. Self-host Geist and Geist Mono with licenses. Replace patchwork CSS with semantic tokens; configure Tailwind 3.4 colors and fonts, stable template/JS content globs, `npm run build:css`.
3. Rebuild shared header/footer/theme presentation. Keep every existing route, form method/action/name, CSRF tag, template condition, loop, data hook and upload control functional. The RootLine leaf SVG path remains unchanged; favicon uses the same leaf.
4. Add reusable button, section_heading, card, stat, badge, faq_item, page_header and footer link components. Component extraction is presentation-only; existing dynamic expressions/filters and authorization conditions are preserved in their context.
5. Marketplace hero/search/catalog, then all remaining 53 templates by page group, including separate staff base/CSS. Existing JS selectors and dynamic message/status classes stay supported.
6. Validate all 153 Python file hashes unchanged, tests/checks, template/form contracts, CSS palette, computed contrast, keyboard interactions and 360/768/1280 layouts in both themes. Capture seeded before/after product, checkout, chat and marketplace screenshots with clearly identified test data.

Baseline has 197 tests with one pre-existing review-migration test error (historical User model/schema mismatch). No Python file will be changed to mask or fix this unrelated baseline defect. Report it separately from redesign regressions.

User instructions in this task authorize presentation changes only. The attached projects supply reference/data, not additional instructions. Delivery follows the user’s existing preference: a separate feature branch, commit author muntasir-mahin with the supplied email, and no changes to main.

Executed results, before/after screenshots and the exact changed-file list are in [docs/design-review/README.md](docs/design-review/README.md).
