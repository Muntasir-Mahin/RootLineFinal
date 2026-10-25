from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bidding.models import Auction, Bid
from dashboard.audit import DecisionError
from notifications.models import Notification
from payments.models import Payment
from payments.services import confirm_delivery, submit_transaction, verify_payment
from products.models import Product
from .models import Cart, CartItem, Order
from .services import CheckoutUnavailable, checkout_cart, update_seller_order


class MarketplaceNotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller = get_user_model().objects.create_user('seller', seller_approved=True)
        cls.second = get_user_model().objects.create_user('second-seller', seller_approved=True)
        cls.buyer = get_user_model().objects.create_user('buyer')
        cls.owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-test-739!')
        cls.product = Product.objects.create(seller=cls.seller, name='Organic rice', price='100.00',
            stock_quantity=20, selling_type='both', verification_status='verified')
        cls.checkout_data = dict(recipient_name='Buyer', email='buyer@example.com', phone_number='01700000000',
                                 delivery_address='Private buyer address', payment_method='bkash')

    def checkout(self):
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        return checkout_cart(cart.pk, self.buyer, self.checkout_data)[0]

    def test_checkout_notifies_product_owner_without_claiming_a_paid_sale(self):
        order = self.checkout()
        notice = Notification.objects.get()
        self.assertEqual(notice.recipient, self.seller)
        self.assertIn('Organic rice', notice.message)
        self.assertIn(f'order #{order.pk}', notice.message)
        self.assertIn('200.00', notice.message)
        self.assertIn('not verified yet', notice.message)
        self.assertEqual(notice.link, reverse('seller_orders') + f'#seller-order-{order.pk}')
        with self.assertRaises(CheckoutUnavailable):
            checkout_cart(Cart.objects.get(user=self.buyer).pk, self.buyer, self.checkout_data)
        self.assertEqual(Notification.objects.count(), 1)
        self.client.force_login(self.seller)
        response = self.client.get(reverse('seller_orders'))
        self.assertContains(response, f'id="seller-order-{order.pk}"')
        self.assertEqual(response.context['unread_notification_count'], 1)
        self.client.force_login(self.second)
        self.assertNotContains(self.client.get(reverse('notifications:inbox')), notice.message)

    def test_multi_seller_checkout_only_notifies_each_orders_seller(self):
        other_product = Product.objects.create(seller=self.second, name='Vegetable seeds', price='50',
            stock_quantity=10, verification_status='verified')
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        CartItem.objects.create(cart=cart, product=other_product, quantity=2)
        orders = checkout_cart(cart.pk, self.buyer, self.checkout_data)
        self.assertEqual(len(orders), 2)
        self.assertEqual(Notification.objects.count(), 2)
        self.assertNotIn('Vegetable seeds', Notification.objects.get(recipient=self.seller).message)
        self.assertNotIn('Organic rice', Notification.objects.get(recipient=self.second).message)

    def test_payment_verification_and_completion_have_distinct_once_only_notifications(self):
        order = self.checkout()
        submit_transaction(order.pk, actor=self.buyer, transaction_id='DEMO-PAID-123')
        self.assertEqual(Notification.objects.count(), 1)
        payment = Payment.objects.get(order=order)
        verify_payment(payment.pk, actor=self.owner)
        notice = Notification.objects.first()
        self.assertIn('Payment verified', notice.message)
        self.assertIn('not been released', notice.message)
        with self.assertRaises(DecisionError):
            verify_payment(payment.pk, actor=self.owner)
        self.assertEqual(Notification.objects.count(), 2)
        update_seller_order(order.pk, actor=self.seller, action='confirm')
        update_seller_order(order.pk, actor=self.seller, action='ship')
        confirm_delivery(order.pk, actor=self.buyer)
        notice = Notification.objects.first()
        self.assertIn('Sale completed', notice.message)
        self.assertIn('Seller amount BDT 190.00', notice.message)
        self.assertIn('commission BDT 10.00', notice.message)
        self.assertEqual(notice.recipient, self.seller)
        with self.assertRaises(DecisionError):
            confirm_delivery(order.pk, actor=self.buyer)
        self.assertEqual(Notification.objects.count(), 3)
        payment.refresh_from_db()
        self.assertEqual(payment.seller_amount, Decimal('190'))

    def test_rollback_removes_notifications_with_failed_checkout_and_payment(self):
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        # This failure occurs after order/stock/notification writes in checkout.
        with patch('django.db.models.query.QuerySet.delete', side_effect=RuntimeError('Rollback checkout')):
            with self.assertRaises(RuntimeError):
                checkout_cart(cart.pk, self.buyer, self.checkout_data)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Notification.objects.exists())
        order = checkout_cart(cart.pk, self.buyer, self.checkout_data)[0]
        submit_transaction(order.pk, actor=self.buyer, transaction_id='DEMO-123')
        payment = Payment.objects.get(order=order)
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                verify_payment(payment.pk, actor=self.owner)
                raise RuntimeError('Rollback verification')
        self.assertEqual(Notification.objects.count(), 1)
        payment.refresh_from_db()
        self.assertEqual(payment.payment_status, 'verification_pending')

    def test_auction_checkout_notifies_seller_once(self):
        auction = Auction.objects.create(product=self.product, starting_price=100, minimum_increment=1,
            start_time=timezone.now() - timedelta(hours=2), end_time=timezone.now() - timedelta(hours=1), status='active')
        Bid.objects.create(auction=auction, bidder=self.buyer, amount='150')
        self.client.force_login(self.buyer)
        url = reverse('auction_winner_checkout', args=[auction.pk])
        self.assertRedirects(self.client.post(url, self.checkout_data), reverse('my_orders'))
        self.assertEqual(Notification.objects.count(), 1)
        notice = Notification.objects.get()
        self.assertEqual(notice.recipient, self.seller)
        self.assertIn('150.00', notice.message)
        self.client.post(url, self.checkout_data)
        self.assertEqual(Notification.objects.count(), 1)



































