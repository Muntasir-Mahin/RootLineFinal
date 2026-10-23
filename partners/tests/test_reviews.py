from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from partners.models import CompanyReview, OrderRequest, PartnerAuditLog, ReviewReport
from partners.order_services import company_order_decision, complete_order, request_order
from partners.review_services import create_review, moderate_review, reply_to_review, report_review
from .helpers import make_company, make_product


class PartnerReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company()
        cls.other = make_company('Other farm')
        cls.product = make_product(cls.company)
        cls.buyer = get_user_model().objects.create_user('review-buyer', email='buyer@example.com')
        cls.stranger = get_user_model().objects.create_user('other-buyer')
        cls.owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-demo-942!')

    def setUp(self):
        cache.clear()

    def order(self, complete=True):
        order = request_order(self.product.pk, buyer=self.buyer, data={
            'quantity':1, 'phone':'01876543210', 'delivery_address':'Private buyer address'})
        if complete:
            company_order_decision(order.pk, actor=self.company.user, decision='accept')
            complete_order(order.pk, actor=self.company.user, final_amount='100')
            order.refresh_from_db()
        return order

    def review(self, rating=5, **kwargs):
        return create_review(self.order().pk, buyer=self.buyer,
            data={'rating':rating, 'title':kwargs.get('title', 'Healthy seeds'),
                  'comment':kwargs.get('comment', 'The order arrived as agreed.')})

    def test_only_completed_order_buyer_can_review_and_one_review_per_order(self):
        data = {'rating':5, 'title':'Seeds', 'comment':'Good quality'}
        order = self.order(complete=False)
        with self.assertRaises(ValidationError):
            create_review(order.pk, buyer=self.buyer, data=data)
        with self.assertRaises(PermissionDenied):
            create_review(order.pk, buyer=self.stranger, data=data)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse('partners:review_create', args=[order.pk])).status_code, 404)
        company_order_decision(order.pk, actor=self.company.user, decision='accept')
        complete_order(order.pk, actor=self.company.user, final_amount='100')
        url = reverse('partners:review_create', args=[order.pk])
        self.assertRedirects(self.client.post(url, data), reverse('partners:buyer_order', args=[order.pk]))
        with self.assertRaises(ValidationError):
            create_review(order.pk, buyer=self.buyer, data=data)
        self.client.post(url, data)
        self.assertEqual(CompanyReview.objects.filter(order=order).count(), 1)
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(url, data).status_code, 404)
        self.assertEqual(self.client.get(reverse('partners:company_reviews')).status_code, 403)

    def test_invalid_rating_and_self_review_are_rejected(self):
        order = self.order()
        with self.assertRaises(ValidationError):
            create_review(order.pk, buyer=self.buyer, data={'rating':6, 'title':'Invalid', 'comment':'Rating out of range'})
        # Even a malformed legacy/admin-created order cannot enable a self-review.
        OrderRequest.objects.filter(pk=order.pk).update(buyer=self.company.user)
        with self.assertRaises(ValidationError):
            create_review(order.pk, buyer=self.company.user, data={'rating':5, 'title':'Self', 'comment':'Not allowed'})
        self.assertFalse(CompanyReview.objects.exists())

    def test_public_ratings_counts_and_hidden_review_exclusion_and_escaping(self):
        first = self.review(5, title='<script>alert(1)</script>')
        second = self.review(3)
        make_product(self.company, name='Second product')
        response = self.client.get(reverse('partners:directory'))
        self.assertContains(response, '4.0 / 5 · 2 reviews')
        company = next(item for item in response.context['page'] if item.pk == self.company.pk)
        self.assertEqual(company.product_count, 2)
        response = self.client.get(self.company.get_absolute_url())
        self.assertContains(response, 'Verified purchase')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertEqual(response.context['ratings']['count'], 2)
        self.assertEqual(dict(response.context['rating_breakdown']), {5:1, 4:0, 3:1, 2:0, 1:0})
        with self.assertRaises(PermissionDenied):
            moderate_review(second.pk, actor=self.company.user, visible=False, reason='Do not like it')
        with self.assertRaises(ValidationError):
            moderate_review(second.pk, actor=self.owner, visible=False, reason='')
        moderate_review(second.pk, actor=self.owner, visible=False, reason='Reviewed reported spam')
        response = self.client.get(self.company.get_absolute_url())
        self.assertEqual(response.context['ratings']['count'], 1)
        self.assertEqual(response.context['ratings']['average'], 5)
        self.assertContains(self.client.get(reverse('partners:directory')), '5.0 / 5 · 1 review')
        self.assertTrue(PartnerAuditLog.objects.filter(action='review.hide', reason='Reviewed reported spam').exists())
        self.client.force_login(self.owner)
        self.client.post(reverse('admin:partners_companyreview_changelist'), {
            'action':'show_reviews', '_selected_action':[str(second.pk)], 'reason':'Appeal checked'})
        second.refresh_from_db()
        self.assertTrue(second.is_visible)

    def test_company_one_public_reply_and_cross_company_isolation(self):
        review = self.review()
        url = reverse('partners:review_reply', args=[review.pk])
        self.client.force_login(self.other.user)
        self.assertEqual(self.client.post(url, {'reply':'Forged'}).status_code, 404)
        with self.assertRaises(PermissionDenied):
            reply_to_review(review.pk, actor=self.other.user, reply='Forged')
        self.client.force_login(self.company.user)
        self.assertRedirects(self.client.post(url, {'reply':'Thank you for your feedback.'}), reverse('partners:company_reviews'))
        with self.assertRaises(ValidationError):
            reply_to_review(review.pk, actor=self.company.user, reply='Second reply')
        self.assertContains(self.client.get(self.company.get_absolute_url()), 'Thank you for your feedback.')
        review.refresh_from_db()
        self.assertIsNotNone(review.replied_at)

    def test_reports_authentication_deduplication_and_private_reasons(self):
        review = self.review()
        url = reverse('partners:review_report', args=[review.pk])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.stranger)
        self.assertRedirects(self.client.post(url, {'reason':'Please check this private report'}),
            self.company.get_absolute_url() + '#partner-reviews')
        report_review(review.pk, reporter=self.stranger, reason='Retry')
        self.assertEqual(ReviewReport.objects.count(), 1)
        self.assertNotContains(self.client.get(self.company.get_absolute_url()), 'Please check this private report')
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse('admin:partners_reviewreport_change', args=[ReviewReport.objects.get().pk])),
            'Please check this private report')
        moderate_review(review.pk, actor=self.owner, visible=False, reason='Spam verified')
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_review_throttling_and_csrf(self):
        order = self.order()
        key = f'partners:review-submissions:{self.buyer.pk}'
        cache.set(key, 10, 3600)
        with self.assertRaisesMessage(ValidationError, 'Too many review attempts'):
            create_review(order.pk, buyer=self.buyer, data={'rating':5, 'title':'Seeds', 'comment':'Good'})
        self.assertFalse(CompanyReview.objects.exists())
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.buyer)
        self.assertEqual(client.post(reverse('partners:review_create', args=[order.pk]),
            {'rating':5, 'title':'Seeds', 'comment':'Good'}).status_code, 403)

    def test_review_pagination_preserves_product_filters(self):
        for index in range(7):
            self.review(title=f'Review {index}')
        response = self.client.get(self.company.get_absolute_url(), {'reviews_page':2, 'sort':'price_low', 'q':'seeds'})
        self.assertEqual(len(response.context['review_page']), 1)
        self.assertContains(response, 'sort=price_low')
        self.assertContains(response, 'reviews_page=1')
        self.assertNotContains(response, '??')
