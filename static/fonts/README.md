# Self-hosted Geist

Geist Sans and Geist Mono variable WOFF2 files are redistributed from the official `geist@1.8.1` npm package (Vercel / Basement Studio), retrieved through npm with integrity verification. See `OFL.txt` for the SIL Open Font License and copyright notices.

Only the font assets are included. RootLine does not depend on the package's Next.js helpers, React, Vite or Google Fonts. Both files are served through Django static files and use `font-display: swap`.

Noto Sans Bengali 400/600/700: self-hosted Bengali subset from @fontsource/noto-sans-bengali@5.3.0 (SIL OFL; accompanying license). No runtime font CDN requests.
