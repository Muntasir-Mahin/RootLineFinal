# Registration camera photo

Branch: `feature/registration-camera-photo`, based on `fix/partner-application-flow`
at `a507bf6`. This work has not been merged into another branch.

## Use and test

1. Start the app with `python manage.py runserver` and open
   `http://127.0.0.1:8000/register/` on the same computer.
2. Hard refresh with **Cmd + Shift + R**. Choose File still selects an existing image.
3. Select **Take photo**, then allow camera access. No microphone is requested.
4. Select **Use photo** to use the current frame as the avatar. Select **Take photo**
   again to retake it. **Cancel** or Escape closes the camera and keeps the
   previously selected photo.
5. Complete registration and check the profile picture after signing in. The
   photo uploads only when the registration form is submitted; the live stream
   stays in the browser. Django's existing image validation and storage apply.
6. Deny camera permission and confirm the explanation appears and Choose File
   still works. Enable permission again in the browser's site settings to retry.

Camera access requires a supported browser and **HTTPS**, except for localhost
or `127.0.0.1` on the same device. A phone opening a computer's plain HTTP LAN
address normally cannot use the camera; test the phone on an HTTPS deployment.
On macOS, also allow the browser under System Settings → Privacy & Security →
Camera if necessary. A missing/busy camera shows an explanation instead of
preventing registration.

There are no new packages, environment variables, migrations, or CSS build
steps. Production deployments must collect the new static JS file using their
usual `python manage.py collectstatic --noinput` step. Like the existing upload,
the photo must be selected again if server validation redisplays the form.

## Changed files

- `accounts/templates/accounts/register.html`: camera controls and page-specific
  script, using existing Tailwind utilities and button styles.
- `static/js/register-camera.js`: explicit camera permission, live preview,
  JPEG capture into the existing file input, cancellation/error handling, and
  camera cleanup on capture, cancellation, submission, hiding, and navigation.
- `docs/registration-camera.md`: usage, requirements, test results, file inventory.

## Verification

- Existing `accounts` test suite: **22 tests passed**.
- Chromium browser checks using a simulated camera: JPEG capture and actual
  registration, stored image verification (JPEG, 1280 × 960), existing upload
  preview, retake cancellation, Escape/focus, permission denial, missing camera,
  late permission resolution after cancellation, and mobile viewport without
  horizontal overflow. Mobile and dark-theme screenshots were inspected.
- Django system checks, JavaScript syntax check, and whitespace checks passed.

Physical camera hardware and iOS/Safari were not available for automated testing;
test those devices using the steps above before deployment.
