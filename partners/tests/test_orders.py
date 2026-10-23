from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from partners.models import LedgerAdjustment, OrderRequest, SalesLedger
from partners.order_services import (adjust_ledger, buyer_evidence, cancel_order,
    company_order_decision, complete_order, report_manual_sale, request_order)
from .helpers import make_company, make_product


class PartnerOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company()
        cls.other = make_company('Other farm')
        cls.product = make_product(cls.company, discount_price='80')
        cls.buyer = get_user_model().objects.create_user('order-buyer', email='buyer@example.com', password='Buyer-demo-732!')
        cls.owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-demo-942!')

    def order(self):
        return request_order(self.product.pk, buyer=self.buyer, data={
            'quantity':Decimal('2'), 'phone':'01876543210', 'delivery_address':'Buyer private address', 'note':'Handle carefully.'})

    def completed(self):
        order = self.order()
        company_order_decision(order.pk, actor=self.company.user, decision='accept')
        ledger = complete_order(order.pk, actor=self.company.user, final_amount='160')
        return order, ledger

    def test_request_snapshot_accept_and_contact_privacy_and_stock(self):
        order = self.order()
        self.assertEqual(order.expected_amount, Decimal('160'))
        self.assertEqual(order.unit_price, Decimal('80'))
        self.client.force_login(self.company.user)
        url = reverse('partners:company_order', args=[order.pk])
        response = self.client.get(url)
        self.assertNotContains(response, order.phone)
        self.assertNotContains(response, order.delivery_address)
        self.assertRedirects(self.client.post(url, {'action':'accept'}), url)
        self.assertContains(self.client.get(url), order.phone)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal('48'))
        cancel_order(order.pk, buyer=self.buyer)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal('50'))

    def test_complete_once_requires_reason_and_company_cannot_edit_ledger(self):
        order = self.order()
        with self.assertRaises(ValidationError):
            complete_order(order.pk, actor=self.company.user, final_amount='160')
        company_order_decision(order.pk, actor=self.company.user, decision='accept')
        with self.assertRaises(ValidationError):
            complete_order(order.pk, actor=self.company.user, final_amount='150')
        ledger = complete_order(order.pk, actor=self.company.user, final_amount='150', reason='Agreed quantity discount.')
        again = complete_order(order.pk, actor=self.company.user, final_amount='160')
        self.assertEqual(ledger.pk, again.pk)
        self.assertEqual(SalesLedger.objects.count(), 1)
        self.assertEqual(SalesLedger.objects.get().amount, Decimal('150'))
        self.client.force_login(self.company.user)
        self.assertEqual(self.client.post(reverse('partners:ledger'), {'amount':'1'}).status_code, 405)
        with self.assertRaises(PermissionDenied):
            adjust_ledger(ledger.pk, actor=self.company.user, amount='1', reason='Not allowed')

    def test_buyer_confirmation_dispute_and_audited_admin_adjustment(self):
        order, ledger = self.completed()
        buyer_evidence(order.pk, buyer=self.buyer, confirm=True)
        ledger.refresh_from_db()
        self.assertIsNotNone(ledger.buyer_confirmed_at)
        buyer_evidence(order.pk, buyer=self.buyer, reason='Actually paid 155', claimed_amount='155')
        ledger.refresh_from_db()
        self.assertTrue(ledger.needs_review)
        self.assertIsNone(ledger.buyer_confirmed_at)
        with self.assertRaises(ValidationError):
            adjust_ledger(ledger.pk, actor=self.owner, amount='155', reason='')
        adjust_ledger(ledger.pk, actor=self.owner, amount='155', reason='Reviewed buyer and company records.', resolve=True)
        ledger.refresh_from_db()
        self.assertEqual(ledger.amount, Decimal('155'))
        self.assertEqual(ledger.original_amount, Decimal('160'))
        self.assertFalse(ledger.needs_review)
        self.assertTrue(LedgerAdjustment.objects.filter(ledger=ledger, previous_amount=160, new_amount=155).exists())

    def test_company_and_buyer_cannot_access_other_orders(self):
        order = self.order()
        self.client.force_login(self.other.user)
        self.assertEqual(self.client.get(reverse('partners:company_order', args=[order.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('partners:company_order', args=[order.pk]), {'action':'accept'}).status_code, 404)
        with self.assertRaises(PermissionDenied):
            company_order_decision(order.pk, actor=self.other.user, decision='accept')
        stranger = get_user_model().objects.create_user('stranger')
        self.client.force_login(stranger)
        self.assertEqual(self.client.get(reverse('partners:buyer_order', args=[order.pk])).status_code, 404)
        with self.assertRaises(PermissionDenied):
            cancel_order(order.pk, buyer=stranger)

    def test_self_order_and_insufficient_stock_are_rejected(self):
        with self.assertRaises(ValidationError):
            request_order(self.product.pk, buyer=self.company.user, data={
                'quantity':1, 'phone':'01876543210', 'delivery_address':'Test'})
        order = self.order()
        self.product.stock_quantity = 1
        self.product.save()
        with self.assertRaises(ValidationError):
            company_order_decision(order.pk, actor=self.company.user, decision='accept')
        order.refresh_from_db()
        self.assertEqual(order.status, 'requested')

    def test_manual_sale_is_separate_and_has_no_verified_buyer_evidence(self):
        ledger = report_manual_sale(self.company.pk, actor=self.company.user,
            data={'amount':'500', 'sale_date':timezone.localdate(), 'reference':'Phone sale reference A'})
        self.assertEqual(ledger.source, 'manual')
        self.assertIsNone(ledger.order_id)
        self.assertIsNone(ledger.buyer_confirmed_at)
        with self.assertRaises(PermissionDenied):
            report_manual_sale(self.company.pk, actor=self.other.user,
                data={'amount':'500', 'sale_date':timezone.localdate(), 'reference':'Forged'})

    def test_buyer_order_request_view_and_protected_product_deletion(self):
        url = reverse('partners:order_create', args=[self.company.slug, self.product.slug])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.buyer)
        response = self.client.post(url, {'quantity':'2', 'phone':'01876543210',
            'delivery_address':'Buyer private address', 'note':'Please call after accepting.'})
        order = OrderRequest.objects.get()
        self.assertRedirects(response, reverse('partners:buyer_order', args=[order.pk]))
        self.client.force_login(self.company.user)
        self.client.post(reverse('partners:product_delete', args=[self.product.pk]))
        self.assertTrue(self.company.products.filter(pk=self.product.pk).exists())
