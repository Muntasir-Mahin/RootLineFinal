# Seller product image fix

The seller's `/products/my-products/` template displayed product metadata and action buttons but never rendered `product.image`. The upload form already used `multipart/form-data`, and the edit view already bound `request.FILES` correctly. This was a missing display block in the seller list, not evidence that every upload had failed.

The seller list now displays the stored image in a linked, lazy-loaded 4:3 thumbnail, or a leaf and `No photo uploaded` fallback. Product details and all seller/auction action links remain intact. No production Python code, URL, upload/storage setting, form field, model or migration changed.

Validation:

- Three image regression tests cover replacement upload persistence, image rendering on seller list/detail, text-only edits retaining the existing image, and explicit image clearing showing the placeholder.
- `python manage.py test products accounts rootline --noinput`: **34 passed**.
- System check, Tailwind build, palette check and whitespace check pass.
- A real browser uploaded a PNG through the existing edit form. The image was saved, served from `/media/` with HTTP 200, and retained through a second edit without a new file.
- Light/dark × 360/768/1280: all six states show a decoded 640×480 image in a 4:3 container with no page overflow or JavaScript errors. [Browser results](browser-results.json).
- The screenshots use a simple palette test pattern in an isolated fixture database, not a customer's product photo. [Desktop](card-light-1280.png) · [Mobile](card-light-360.png) · [Dark desktop](card-dark-1280.png).

To update an existing ZIP folder, replace `products/templates/products/my_products.html` with the updated template, save, and refresh the seller list. Existing saved images then appear automatically; no re-upload is needed if the file was already saved. A missing file on disk or production media-serving error would require a separate storage diagnosis; no such failure was reproduced in the verified upload path.
