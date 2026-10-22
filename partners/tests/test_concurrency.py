from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import skipIf

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import connection, connections
from django.test import TransactionTestCase
from django.utils import timezone

from partners.billing_services import generate_invoice, month_start
from partners.models import BillingPlan, Invoice, SalesLedger
from partners.order_services import company_order_decision, complete_order, request_order
from partners.review_services import create_review
from .helpers import make_company, make_product


@skipIf(connection.vendor == 'sqlite' and connection.creation.is_in_memory_db(connection.settings_dict['NAME']),
        'Concurrency needs a real file: set ROOTLINE_TEST_DB=/tmp/rootline-partners-tests.sqlite3.')
class PartnerConcurrencyTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        BillingPlan.objects.get_or_create(name='Standard Partner Plan', defaults={'is_default':True})
        self.company = make_company()
        self.product = make_product(self.company)
        self.buyer = get_user_model().objects.create_user('concurrent-buyer')

    def parallel(self, action):
        barrier = Barrier(2)

        def worker():
            connections.close_all()
            barrier.wait(timeout=10)
            try:
                return action()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(worker) for _ in range(2)]
            return [job.result(timeout=30) for job in jobs]

    def completed_order(self):
        order = request_order(self.product.pk, buyer=self.buyer, data={
            'quantity':1, 'phone':'01876543210', 'delivery_address':'Private buyer address'})
        company_order_decision(order.pk, actor=self.company.user, decision='accept')
        return order

    def test_concurrent_completion_and_invoice_have_one_record(self):
        order = self.completed_order()
        self.parallel(lambda: complete_order(order.pk, actor=self.company.user, final_amount='100'))
        self.assertEqual(SalesLedger.objects.filter(order=order).count(), 1)
        self.assertEqual(SalesLedger.objects.get(order=order).amount, Decimal('100'))
        self.parallel(lambda: generate_invoice(self.company.pk, month_start(timezone.localdate())))
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(Invoice.objects.get().total_due, Decimal('5'))

    def test_concurrent_review_keeps_one_verified_purchase(self):
        order = self.completed_order()
        complete_order(order.pk, actor=self.company.user, final_amount='100')

        def review():
            try:
                return create_review(order.pk, buyer=self.buyer,
                    data={'rating':5, 'title':'Seeds', 'comment':'Good quality'})
            except ValidationError:
                return None

        self.parallel(review)
        self.assertEqual(self.company.company_reviews.count(), 1)
