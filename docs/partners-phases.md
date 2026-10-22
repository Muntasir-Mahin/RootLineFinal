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
