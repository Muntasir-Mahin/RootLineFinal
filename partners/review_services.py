from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import CompanyProfile, CompanyReview, OrderRequest, ReviewReport
from .services import audit, require_company_actor, require_owner


def require_buyer(buyer):
    if not buyer.is_authenticated or not buyer.is_active:
        raise PermissionDenied


def throttle_reviews(buyer):
    # A fixed window, shared by retries; production should use a shared cache.
    key = f'partners:review-submissions:{buyer.pk}'
    if cache.add(key, 1, timeout=3600):
        return
    try:
        count = cache.incr(key)
    except ValueError:
        cache.add(key, 1, timeout=3600)
        count = 1
    if count > 10:
        raise ValidationError('Too many review attempts. Please try again in an hour.')


def create_review(order_id, *, buyer, data):
    require_buyer(buyer)
    throttle_reviews(buyer)
    with transaction.atomic():
        company_id = OrderRequest.objects.values_list('company_id', flat=True).get(pk=order_id)
        company = CompanyProfile.objects.select_for_update().get(pk=company_id)
        order = OrderRequest.objects.select_for_update().get(pk=order_id)
        if order.buyer_id != buyer.pk:
            raise PermissionDenied
        if company.user_id == buyer.pk or order.status != 'completed':
            raise ValidationError('Only the buyer of a completed order can leave a verified purchase review.')
        if CompanyReview.objects.filter(order=order).exists():
            raise ValidationError('This order already has a review.')
        review = CompanyReview(order=order, company=company, buyer=buyer,
            rating=data['rating'], title=data['title'].strip(), comment=data['comment'].strip())
        review.full_clean()
        review.save()
        audit(company, buyer, 'review.create', review)
        return review


@transaction.atomic
def reply_to_review(review_id, *, actor, reply):
    company_id = CompanyReview.objects.values_list('company_id', flat=True).get(pk=review_id)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    require_company_actor(company, actor)
    review = CompanyReview.objects.select_for_update().get(pk=review_id)
    if review.reply:
        raise ValidationError('A company can post one public reply per review.')
    if not reply.strip() or len(reply) > 3000:
        raise ValidationError('Write a reply of up to 3000 characters.')
    review.reply, review.replied_at = reply.strip(), timezone.now()
    review.save(update_fields=['reply', 'replied_at'])
    audit(company, actor, 'review.reply', review)
    return review


@transaction.atomic
def report_review(review_id, *, reporter, reason):
    require_buyer(reporter)
    review = CompanyReview.objects.select_related('company').get(pk=review_id, is_visible=True)
    if not CompanyProfile.objects.public().filter(pk=review.company_id).exists():
        raise PermissionDenied
    if not reason.strip() or len(reason) > 2000:
        raise ValidationError('Give a report reason of up to 2000 characters.')
    report, created = ReviewReport.objects.get_or_create(review=review, reporter=reporter,
                                                        defaults={'reason':reason.strip()})
    if created:
        audit(review.company, reporter, 'review.report', report)
    return report


@transaction.atomic
def moderate_review(review_id, *, actor, visible, reason):
    require_owner(actor)
    if not reason.strip():
        raise ValidationError('An owner moderation reason is required.')
    company_id = CompanyReview.objects.values_list('company_id', flat=True).get(pk=review_id)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    review = CompanyReview.objects.select_for_update().get(pk=review_id)
    if review.is_visible != visible:
        review.is_visible = visible
        review.save(update_fields=['is_visible'])
        audit(company, actor, 'review.show' if visible else 'review.hide', review, reason=reason)
    return review
