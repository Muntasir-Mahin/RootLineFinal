# Compact footer contact layout

The four navigation columns stay aligned. Direct contact details move into a separate full-width section: three cards on desktop, two columns on tablet (the last card spans the row), and one on small phones. Social channels become compact labelled buttons in a separate wrapping row. Support hours sit beside them where space permits. An odd final social button spans the mobile row.

[Desktop light](footer-light-1280.png) · [Mobile light](footer-light-360.png) · [Tablet light](footer-light-768.png) · [Desktop dark](footer-dark-1280.png) · [Mobile dark](footer-dark-360.png)

The screenshots use disposable demo social links and hours to reproduce the user's eight-channel case. No demo values were added to application settings. Fixed header, bottom navigation and floating controls are hidden **only in these footer-only screenshots** to prevent them obscuring a tall element capture.

Six light/dark/viewport states passed: no page overflow or measured text-contrast failures; all footer tap targets at least 44px; phone/email Copy works; external social links retain their secure new-tab attributes. Existing `rootline` and `accounts` suites: 31 tests pass. Palette scan passes. No business logic, models, migrations or contact settings changes.

## Update an existing downloaded project

The change needs five frontend files, including the new `templates/components/footer_contact.html`. `scripts/update_contact_footer.py` updates just these files, downloads everything before writing, and saves original files under `work/footer-backup-<timestamp>/`.

In your existing RootLine project's PyCharm **Terminal**, run the helper using the commit shown in the chat response. Restart the server and refresh with Command+Shift+R. The helper works with both a Git checkout and a downloaded ZIP folder. It does not require a `.env` file, Git setup or new dependencies. It preserves your settings and database.

If this is a Git checkout, you can instead pull the updated feature branch using your normal workflow. For deployment, release the updated frontend files and run your existing `collectstatic` step.
