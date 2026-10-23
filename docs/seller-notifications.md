# Normal seller and marketplace sale notifications

These notifications reuse the existing bell and `/notifications/` inbox. They are in-app messages; they do not require Gmail/SMTP, send email, or change the payment/seller approval rules. Existing Partner notifications continue separately.

## Events and recipients

| Event | Who receives it | Destination |
| --- | --- | --- |
| Customer submits a new seller request | Active owner/superusers and active staff with the **Catalogue** role | Staff Sellers pending queue |
| Seller request approved | The requesting customer | Seller Dashboard |
| Seller request rejected | The requesting customer, including an optional staff note | Customer profile |
| Seller access revoked | That seller, including an optional staff note | Customer profile |
| Marketplace checkout creates an order | Only that order's seller; message includes product names, order number and amount | That seller's order card |
| Finance/owner verifies the order payment | That order's seller; message clearly says the payment is recorded as held in escrow | That seller's order card |
| Order completes and escrow is released in the records | That order's seller; message includes recorded seller amount and commission | That seller's order card |

Fixed-price cart checkout and auction-winner checkout both send new-order notifications. A multi-seller cart creates a separate order and notification for each corresponding seller. Adding a product to cart, placing a bid, or submitting an unverified transaction ID is not a completed sale.

Example: an order totals BDT 200. The seller first sees **New order**, then **Payment verified** after staff verification. When buyer delivery confirmation (or an authorized dispute resolution) completes the order and releases escrow in RootLine's records, the seller sees **Sale completed**, with BDT 190 seller amount and BDT 10 commission under the existing 5% marketplace commission rule. These messages report the existing bookkeeping state; they do not transfer money through bKash/Nagad or change any calculations.

## How the bell is handled

1. The actual request/order/payment service creates a `Notification` row for the relevant recipient. Its fields remain recipient, message, internal link, unread/read state and creation time.
2. Notification creation shares the business transaction. A rolled-back checkout, approval or verification also rolls back its notification.
3. Existing locks and transition guards prevent duplicate notifications from repeated seller requests, checkout retries, repeated payment verification or repeated completion. A rejected applicant's genuinely new seller request creates a new event.
4. The bell counts **only the signed-in user's unread notifications**. A seller does not see another seller's sale notices; non-Catalogue staff do not receive seller-review notices unless they are an owner.
5. Opening the inbox does not automatically mark items read. **Mark read** is an ownership-checked, CSRF-protected POST; the unread count then decreases.
6. Refresh or navigate to see new counts. This is not live WebSocket delivery, a mobile push notification or email delivery.

Old requests/orders that predate this code are not backfilled. An existing pending seller request remains available in the Sellers queue; new notification events start with requests/actions performed after this update. No existing account/order data is modified by an automatic backfill.

## Setup and manual test

No new migration, package or email setting is needed beyond the existing notifications app setup. Download/pull the updated `fix/partner-application-flow` branch, preserve your `.env`, database and uploads, and restart Django.

1. Sign in as the owner. For a reviewer, enable **Staff status** and assign **Catalogue**, not Partners. In another browser profile, sign in as a normal customer.
2. Choose **Become a Seller**. Refresh the owner/Catalogue dashboard: the seller queue and notification bell should increase. Repeating the same pending request must not add another notice.
3. Approve/reject from the Sellers queue or owner admin. Refresh the customer's inbox: it should show the decision and any staff note. A rejected customer can request again; revocation also notifies the seller.
4. As a buyer, check out a verified product belonging to an approved seller. Refresh that seller's bell: **New order** appears. Click it to jump to the corresponding order card.
5. Submit the payment reference as buyer, then verify it as Finance/owner. The seller gets **Payment verified**, with escrow still held.
6. Follow the existing confirm → ship → buyer-confirm-delivery flow. The seller gets **Sale completed**, with the recorded net amount and commission. Refreshing/retrying a completed action must not add another completion notice.
7. Mark notices read and check the bell count. Sign in as another seller/customer: the first seller's notices must be absent.

## Changed files

Validation: all 11 new seller/order notification tests passed. Full suite: 298 tests, 297 passed; the unchanged existing `reviews.tests.ReviewMigrationTests` error on `accounts_user.theme_preference` remains. Django system checks, migration drift checks and whitespace checks passed; no new migration is required.

| File | Reason |
| --- | --- |
| `dashboard/services.py` | Add notification hooks only after actual seller requests/decisions. |
| `dashboard/seller_notifications.py` | Select owner/Catalogue recipients and build seller request/decision notices. |
| `dashboard/test_seller_notifications.py` | Test recipients, retries, permissions, admin decisions, resubmission and rollback. |
| `orders/services.py` | Notify the corresponding seller after a cart order and its item snapshots are created. |
| `orders/notifications.py` | Build distinct new-order, verified-payment and completed-sale messages using existing recorded amounts. |
| `orders/test_notifications.py` | Test fixed/auction/multi-seller checkout, ownership, payment/completion states, retries and rollback. |
| `orders/templates/orders/seller_orders.html` | Add only a stable order-card ID so notification links jump to the correct order. |
| `payments/services.py` | Notify after successful verification and escrow release, sharing the existing transactions. |
| `bidding/views.py` | Notify after an auction-winner checkout successfully creates and links its order. |
| `docs/seller-notifications.md` | Explain events, recipients, limits, manual testing and this complete file inventory. |
