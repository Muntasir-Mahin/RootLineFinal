# Agro Partners phase file inventory

Each phase lists every repository file created or modified and why. Existing marketplace models, views, search, cart, checkout, styles and user model are preserved.

## Phase 1 — accounts, profiles and approval

Validation: 8 Partner account/approval/ownership/upload/admin tests passed on Django 6.1.2; migration applied; scoped Tailwind CSS built.

| File | Reason |
| --- | --- |
| `accounts/templates/accounts/login.html` | Add only the Partner Company Login link. |
| `accounts/templates/accounts/register.html` | Add only the separate company registration link. |
| `partners/__init__.py` | Initialize and register the new Django package. |
| `partners/admin.py` | Owner approval actions and model administration. |
| `partners/apps.py` | Initialize and register the new Django package. |
| `partners/forms.py` | Company registration/login/profile and sanitized upload forms. |
| `partners/migrations/0001_initial.py` | Initial database schema for the new app. |
| `partners/migrations/__init__.py` | Initial database schema for the new app. |
| `partners/models.py` | Company profiles, category/asset records and append-only audit model. |
| `partners/services.py` | Registration, role assignment, audited owner decisions and safe notifications. |
| `partners/static/partners/partners.css` | Partner-only Tailwind utility source and compiled asset. |
| `partners/static/partners/source.css` | Partner-only Tailwind utility source and compiled asset. |
| `partners/tailwind.config.js` | Reuse the existing theme, scoped to Partner pages. |
| `partners/templates/partners/assets.html` | New Partner page extending base.html. |
| `partners/templates/partners/base.html` | New Partner page extending base.html. |
| `partners/templates/partners/confirm_delete.html` | New Partner page extending base.html. |
| `partners/templates/partners/dashboard.html` | New Partner page extending base.html. |
| `partners/templates/partners/form.html` | New Partner page extending base.html. |
| `partners/templates/partners/login.html` | New Partner page extending base.html. |
| `partners/templates/partners/register.html` | New Partner page extending base.html. |
| `partners/templates/partners/terms.html` | New Partner page extending base.html. |
| `partners/tests/__init__.py` | Phase 1 regression coverage and isolated test fixtures. |
| `partners/tests/helpers.py` | Phase 1 regression coverage and isolated test fixtures. |
| `partners/tests/test_accounts.py` | Phase 1 regression coverage and isolated test fixtures. |
| `partners/urls.py` | Register Partner Company account/dashboard routes. |
| `partners/validators.py` | Bound image/document size, validate image content and re-encode images. |
| `partners/views.py` | Separate company authentication and owner-scoped profile/asset dashboard. |
| `rootline/settings.py` | Register the isolated partners app. |
| `rootline/urls.py` | Include the partners URL namespace. |
| `docs/partners-phases.md` | Record per-phase checks and the complete changed-file inventory. |

## Phase 2 — products and public Partner Stores

Validation: All 14 Partner tests passed, including marketplace/cart isolation, private contact details, pending/suspended visibility, product ownership, filtering and pagination. Migration applied; scoped Tailwind rebuilt.

| File | Reason |
| --- | --- |
| `docs/partners-phases.md` | Record this phase, verification and the complete file inventory. |
| `partners/admin.py` | Register phase 2 models and owner-only actions. |
| `partners/forms.py` | Add phase 2 input validation without exposing ownership or admin fields. |
| `partners/migrations/0002_companyproduct_companyproductimage_and_more.py` | New phase 2 schema migration; no old marketplace schema edits. |
| `partners/models.py` | Add phase 2 data models, constraints and public-state queries. |
| `partners/product_views.py` | Enforce company ownership on product and image operations. |
| `partners/public_views.py` | Serve approved stores/products using isolated queries and gated contact details. |
| `partners/static/partners/partners.css` | Rebuild only the Partner-scoped Tailwind utility asset. |
| `partners/templates/partners/base.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/contact.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/directory.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/pagination.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/product_card.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/product_detail.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/product_images.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/product_list.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/store.html` | New or updated phase 2 page using existing design classes and scoped Tailwind. |
| `partners/tests/helpers.py` | Phase 2 ownership, isolation and workflow regression tests. |
| `partners/tests/test_stores.py` | Phase 2 ownership, isolation and workflow regression tests. |
| `partners/urls.py` | Register phase 2 namespaced routes before the store slug route. |
| `templates/base.html` | Add only the Agro Partners navbar link. |

## Phase 3 — Order Requests and immutable sales ledger

Validation: All 21 Partner tests passed. Request/accept/complete/cancel, stock reservation/restoration, buyer-phone privacy, one ledger entry per order, buyer confirmation/disputes, manual sale labels and owner-only audited adjustments are covered.

| File | Reason |
| --- | --- |
| `docs/partners-phases.md` | Record this phase, verification and the complete file inventory. |
| `partners/admin.py` | Register phase 3 models and owner-only actions. |
| `partners/migrations/0003_orderrequest_salesledger_ledgeradjustment_and_more.py` | New phase 3 schema migration; no old marketplace schema edits. |
| `partners/models.py` | Add phase 3 data models, constraints and public-state queries. |
| `partners/order_forms.py` | Implement the isolated phase 3 workflow or operational tooling. |
| `partners/order_services.py` | Implement the isolated phase 3 workflow or operational tooling. |
| `partners/order_views.py` | Implement the isolated phase 3 workflow or operational tooling. |
| `partners/services.py` | Add phase 3 transactional and audited business operations. |
| `partners/static/partners/partners.css` | Rebuild only the Partner-scoped Tailwind utility asset. |
| `partners/templates/admin/partners/action_form.html` | New or updated phase 3 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/base.html` | New or updated phase 3 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/dashboard.html` | New or updated phase 3 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/ledger.html` | New or updated phase 3 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/order_action.html` | New or updated phase 3 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/order_detail.html` | New or updated phase 3 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/order_list.html` | New or updated phase 3 page using existing design classes and scoped Tailwind. |
| `partners/templates/partners/product_detail.html` | New or updated phase 3 page using existing design classes and scoped Tailwind. |
| `partners/tests/test_orders.py` | Phase 3 ownership, isolation and workflow regression tests. |
| `partners/urls.py` | Register phase 3 namespaced routes before the store slug route. |
