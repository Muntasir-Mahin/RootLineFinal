# Site controls and voice setup

Shared navigation now includes dark/light mode, search, a responsive menu, a sticky header, a skip link, scroll progress, back-to-top and help/contact controls. The staff dashboard uses the same account theme preference. Reduced-motion preferences are respected. The main navigation and FAQ remain usable without JavaScript.

Search (`/search/?q=rice`) covers names, descriptions and categories of verified, available products with stock, plus titles, summaries and channels of published Agro Updates. Draft/future videos and unavailable products are excluded. Each result group has its own pagination.

Copy controls are on product/video detail pages, help and assistant answers. Browsers require HTTPS or localhost for clipboard access. Destructive product deletion and chat-history clearing use accessible confirmation dialogs with Cancel and Escape. Existing server authorization and CSRF checks still apply.

Forms show submission progress, prevent repeated native submissions and show server-confirmed success messages for registration, profile edits, password changes and seller requests. Failed login shows an error. A submission indicator never claims the server saved a form.

## Cookie preferences and UTM tags

The banner offers **Essential only** or **Allow campaign tracking**. The preference is saved for 180 days in the `rootline_consent` cookie (`SameSite=Lax`; `Secure` on HTTPS). Sign-in and CSRF cookies remain essential. Preferences can be changed in the footer.

Only after campaign consent, `utm_source`, `utm_medium`, `utm_campaign`, `utm_term` and `utm_content` are read from the current URL, bounded to 150 characters each and stored in this tab's `sessionStorage` under `rootline-campaign`. A `rootline:campaign` custom event exposes the same tags for future integration. Essential-only consent removes stored campaign tags. No external analytics requests, identifiers or reporting dashboard are added. Do not put personal data in campaign URLs.

## Floating contact

The help panel links to the FAQ and the existing order-support/dispute flow. Set `ROOTLINE_CONTACT_EMAIL` to your **public support address** to also show an email link. No address or WhatsApp number is invented. Restart Django after changing this environment variable.

## Why the voice buttons were disabled

Both recording and upload require server-side transcription. The buttons intentionally stay disabled when whisper.cpp or its multilingual speech model is absent. Microphone recording additionally requires a supported browser, HTTPS (or localhost) and microphone permission. Uploading a recording does not require microphone access.

The page now explains missing speech tools/models, offers voice help, supports recording uploads without JavaScript when the server is ready, and refreshes availability using **Check connection**. A failed status request clears stale readiness. Text entry remains available.

### Linux / source build

Requires Python 3.12+, git, curl, a C++ compiler, make and ffmpeg. From the project root, after installing Django/Pillow in `.venv`:

```sh
bash scripts/setup_voice.sh
. work/voice.env
.venv/bin/python manage.py check_voice
.venv/bin/python manage.py runserver
```

This builds whisper.cpp v1.8.2 with two compiler jobs and downloads multilingual Whisper **small** (about 466 MiB). The download is checked against the hash in that pinned upstream release before replacing a model. Tools go under ignored `work/voice-runtime`, models under ignored `local_models/`, and only nonsecret executable/model paths go into ignored `work/voice.env`. Existing files are preserved until a verified replacement is available. `--tools-only` prepares the executable without downloading the model.

In a restricted cloud environment, allow `huggingface.co` and its model-download redirect hosts (`cdn-lfs.huggingface.co`, `cdn-lfs-us-1.hf.co`, `cas-bridge.xethub.hf.co`). The current instance built Whisper successfully using `/workspace/.rootline-tools`, but the model request returned proxy HTTP 403. Those domain additions were saved in the environment draft; saving a draft does not apply its network policy. After applying the policy, run:

```sh
ROOTLINE_VOICE_TOOLS=/workspace/.rootline-tools bash scripts/setup_voice.sh
. work/development.env
. work/voice.env
.venv/bin/python manage.py check_voice
# Restart the running Django process with these variables.
```

Then test an actual recording:

```sh
.venv/bin/python manage.py check_voice --audio /path/to/question.wav --language bn
```

On macOS you can instead use the existing `chatbot/README.md` Homebrew instructions (`brew install whisper.cpp ffmpeg`) and configure `WHISPER_CLI`/`WHISPER_MODEL_PATH` in your IDE. Sourcing `work/voice.env` in a terminal does not change an already running IDE process.

Whisper transcribes speech. Ollama + Gemma generate answers and are still separate prerequisites for sending chat questions. No cloud speech fallback is added.

## Validation

```sh
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
ROOTLINE_TEST_DB=work/site-tests.sqlite3 .venv/bin/python manage.py test rootline accounts chatbot --noinput
```

Browser checks exercised consent/UTM, guest/account themes, mobile menu, scroll controls, search, FAQ, copy, help, Cancel/Escape and recording/upload controls. Recording and upload checks used explicit simulated server responses; they do not demonstrate real model transcription. Real inference remains blocked until the speech model is installed.

The full suite has an existing failure in `reviews.tests.ReviewMigrationTests.test_duplicate_reviews_block_migration_without_deleting_data`: the historical user model lacks the newer `theme_preference` column while the database still has it. This change does not alter that migration test.

## Commit with your own GitHub identity

For future local commits, replace the email placeholder with a verified address from **GitHub → Settings → Emails**, or copy your exact private `noreply` address from that page. GitHub attributes commits by email; changing `user.name` alone is insufficient.

```sh
cd /path/to/RootLineFinal
# Only if moving this cloud patch to a separate checkout:
git apply --check /path/to/rootline-improvements.patch
git apply /path/to/rootline-improvements.patch

git config --local user.name "muntasir-mahin"
git config --local user.email "YOUR_VERIFIED_GITHUB_EMAIL"
git var GIT_AUTHOR_IDENT
git status --short
git diff --check
git add accounts/views.py agro_updates/templates/agro_updates/detail.html \
  chatbot dashboard/static/dashboard/dashboard.css dashboard/templates/dashboard/base.html dashboard/tests.py \
  products/templates/products/delete_product.html products/templates/products/marketplace_product_detail.html \
  rootline templates/base.html templates/site static/css/site-tools.css \
  static/js/site-tools.js static/js/theme-init.js static/js/theme-toggle.js scripts/setup_voice.sh docs/site-improvements.md
git diff --cached --stat
git commit -m "Improve site navigation, feedback, themes and voice setup"
```

Do not stage `.env`, `.venv`, `work/`, databases, uploaded media, model files or credentials. These are ignored already. Git authentication and commit author identity are separate settings. There is no push step above.
