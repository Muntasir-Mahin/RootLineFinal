from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from bidding.models import Auction
from products.models import Product
from .audit import DecisionError, record_action
from .seller_notifications import product_reviewed, seller_decided, seller_requested


@transaction.atomic
def review_product(product_id, *, actor, decision, note=''):
    if decision not in ('verified', 'rejected', 'pending'):
        raise DecisionError('Choose Verify, Reject, or Unverify / send back to review.')
    product = Product.objects.select_for_update().get(pk=product_id)
    previous = product.verification_status
    if previous == decision:
        raise DecisionError(f'This product is already {decision}; choose a different status.')
    note = note.strip()
    if len(note) > 4000:
        raise DecisionError('The note must be at most 4,000 characters.')
    if (previous == 'verified' or decision == 'rejected') and not note:
        raise DecisionError('A reason is required when rejecting or unverifying a product.')
    if previous == 'verified':
        # Match bidding and auction checkout: lock Product before Auction. The
        # product lock also prevents new bids racing with this decision.
        auction = Auction.objects.select_for_update().filter(product=product).first()
        if (auction and auction.status != 'cancelled' and not auction.order_id
                and auction.bids.exists()):
            raise DecisionError(
                'This product has unsettled auction bids. Settle the auction before '
                'rejecting or unverifying it; bids and winner checkout must be preserved.'
            )
    product.verification_status = decision
    product.save(update_fields=['verification_status', 'updated_at'])
    record_action(actor=actor, action=f'product.{decision}', target=product,
                  summary=f'Product #{product.pk}: {previous} → {decision}: {product.name}'[:255], note=note)
    product_reviewed(product, previous, note)
    return product


@transaction.atomic
def review_seller(user_id, *, actor, decision, note=''):
    seller = get_user_model().objects.select_for_update().get(pk=user_id)
    if decision in ('approve', 'reject'):
        if not seller.seller_requested or seller.seller_approved:
            raise DecisionError('This user has no pending seller request.')
        seller.seller_approved = decision == 'approve'
        seller.seller_requested = False
        seller.seller_requested_at = None
    elif decision == 'revoke':
        if not seller.seller_approved:
            raise DecisionError('Only an approved seller can be revoked.')
        seller.seller_approved = False
        seller.seller_requested = False
        seller.seller_requested_at = None
    else:
        raise DecisionError('Choose Approve, Reject or Revoke.')
    seller.save(update_fields=['seller_approved', 'seller_requested', 'seller_requested_at'])
    record_action(actor=actor, action=f'seller.{decision}', target=seller,
                  summary=f'Seller {decision}: {seller.get_username()}', note=note)
    seller_decided(seller, decision, note)
    return seller


@transaction.atomic
def request_seller_access(user_id):
    seller = get_user_model().objects.select_for_update().get(pk=user_id)
    if not seller.seller_requested and not seller.seller_approved:
        seller.seller_requested = True
        seller.seller_requested_at = timezone.now()
        seller.save(update_fields=['seller_requested', 'seller_requested_at'])
        seller_requested(seller)
