from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from .audit import DecisionError
from .services import request_seller_access, review_seller


class SellerNotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = get_user_model().objects.create_user('customer')
        cls.owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-test-739!')
        cls.catalogue = get_user_model().objects.create_user('catalogue', is_staff=True)
        cls.support = get_user_model().objects.create_user('support', is_staff=True)
        cls.inactive = get_user_model().objects.create_user('inactive', is_staff=True, is_active=False)
        cls.nonstaff = get_user_model().objects.create_user('nonstaff')
        group, _ = Group.objects.get_or_create(name='Catalogue')
        for user in (cls.catalogue, cls.inactive, cls.nonstaff):
            user.groups.add(group)
        # Multiple eligible groups must not create duplicate recipient rows.
        extra, _ = Group.objects.get_or_create(name='Support')
        cls.catalogue.groups.add(extra)
        cls.support.groups.add(extra)

    def test_request_notifies_only_owner_and_active_catalogue_staff_once(self):
        self.client.force_login(self.customer)
        self.assertRedirects(self.client.post(reverse('become_seller')), reverse('profile'))
        self.client.post(reverse('become_seller'))
        self.assertEqual(set(Notification.objects.values_list('recipient_id', flat=True)),
                         {self.owner.pk, self.catalogue.pk})
        self.assertEqual(Notification.objects.count(), 2)
        self.assertIn(self.customer.get_username(), Notification.objects.first().message)
        self.assertEqual(Notification.objects.first().link, reverse('dashboard:sellers') + '?tab=requests')
        self.client.force_login(self.catalogue)
        response = self.client.get(reverse('dashboard:overview'))
        self.assertEqual(response.context['unread_notification_count'], 1)
        self.assertEqual(response.context['queue_sizes']['sellers'], 1)

    def test_approval_notifies_customer_and_retry_does_not_duplicate(self):
        request_seller_access(self.customer.pk)
        self.client.force_login(self.catalogue)
        url = reverse('dashboard:seller_decide', args=[self.customer.pk, 'approve'])
        self.assertRedirects(self.client.post(url, {'note':'Details checked'}), reverse('dashboard:sellers'))
        notice = Notification.objects.get(recipient=self.customer)
        self.assertIn('approved', notice.message)
        self.assertIn('Details checked', notice.message)
        self.assertEqual(notice.link, reverse('seller_dashboard'))
        with self.assertRaises(DecisionError):
            review_seller(self.customer.pk, actor=self.catalogue, decision='approve')
        self.assertEqual(Notification.objects.filter(recipient=self.customer).count(), 1)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(notice.link).status_code, 200)

    def test_rejection_resubmission_and_revocation_use_existing_rules(self):
        request_seller_access(self.customer.pk)
        review_seller(self.customer.pk, actor=self.catalogue, decision='reject', note='Please update your address')
        rejected = Notification.objects.get(recipient=self.customer)
        self.assertIn('rejected', rejected.message)
        self.assertIn('Please update your address', rejected.message)
        self.assertEqual(rejected.link, reverse('profile'))
        request_seller_access(self.customer.pk)
        self.assertEqual(Notification.objects.filter(recipient=self.owner).count(), 2)
        review_seller(self.customer.pk, actor=self.catalogue, decision='approve')
        review_seller(self.customer.pk, actor=self.catalogue, decision='revoke', note='Owner review required')
        revoked = Notification.objects.filter(recipient=self.customer).first()
        self.assertIn('revoked', revoked.message)
        self.assertIn('Owner review required', revoked.message)
        self.assertEqual(revoked.link, reverse('profile'))
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_active)
        self.assertFalse(self.customer.seller_approved)

    def test_forbidden_decision_does_not_notify_or_approve(self):
        request_seller_access(self.customer.pk)
        self.client.force_login(self.support)
        self.assertEqual(self.client.post(reverse('dashboard:seller_decide', args=[self.customer.pk, 'approve'])).status_code, 403)
        self.assertFalse(Notification.objects.filter(recipient=self.customer).exists())
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.seller_approved)

    def test_rollback_cannot_leave_request_or_decision_notifications(self):
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                request_seller_access(self.customer.pk)
                raise RuntimeError('Rollback request')
        self.assertFalse(Notification.objects.exists())
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.seller_requested)
        request_seller_access(self.customer.pk)
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                review_seller(self.customer.pk, actor=self.catalogue, decision='approve')
                raise RuntimeError('Rollback decision')
        self.assertFalse(Notification.objects.filter(recipient=self.customer).exists())
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.seller_approved)
        self.assertTrue(self.customer.seller_requested)

    def test_owner_admin_decision_also_notifies_seller(self):
        request_seller_access(self.customer.pk)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(reverse('admin:accounts_user_changelist'), {
            'action':'approve_sellers', '_selected_action':[str(self.customer.pk)], 'note':'Owner checked'
        }).status_code, 302)
        self.assertEqual(Notification.objects.filter(recipient=self.customer).count(), 1)
        self.assertIn('Owner checked', Notification.objects.get(recipient=self.customer).message)
