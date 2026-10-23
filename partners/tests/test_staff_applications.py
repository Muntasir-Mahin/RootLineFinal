from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from dashboard.permissions import PARTNERS
from notifications.models import Notification
from partners.models import CompanyProfile, CustomerEmailVerification, PartnerAuditLog
from partners.services import ROLE_NAME, decide_company, register_company
from partners.storage import PartnerPrivateStorage
from .helpers import make_company


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   STAFF_NOTIFICATION_EMAILS=['extra@example.com', 'reviewer@example.com'])
class PartnerStaffTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = get_user_model().objects.create_user('customer', email='customer@example.com')
        CustomerEmailVerification.objects.create(user=cls.customer, email=cls.customer.email, verified_at=timezone.now())
        cls.owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-test-934!')
        cls.reviewer = get_user_model().objects.create_user('reviewer', email='reviewer@example.com', is_staff=True)
        cls.support = get_user_model().objects.create_user('support', email='support@example.com', is_staff=True)
        cls.inactive = get_user_model().objects.create_user('inactive', email='inactive@example.com', is_staff=True, is_active=False)
        group, _ = Group.objects.get_or_create(name=PARTNERS)
        cls.reviewer.groups.add(group)
        cls.inactive.groups.add(group)
        support, _ = Group.objects.get_or_create(name='Support')
        cls.support.groups.add(support)

    def data(self):
        return dict(company_name='Customer Agro', email='company@example.com', phone='01700000001',
            address='Dhaka', district='Dhaka', division='Dhaka', trade_license='', agree_terms=True)

    def test_submission_notifies_active_partners_staff_owner_and_configured_emails(self):
        self.client.force_login(self.customer)
        count = get_user_model().objects.count()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('partners:apply'), self.data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_user_model().objects.count(), count)
        self.assertEqual(set(Notification.objects.values_list('recipient_id', flat=True)), {self.reviewer.pk, self.owner.pk})
        self.assertEqual({item.to[0] for item in mail.outbox}, {'reviewer@example.com', 'owner@example.com', 'extra@example.com'})
        self.client.force_login(self.reviewer)
        response = self.client.get(reverse('dashboard:overview'))
        self.assertEqual(response.context['queue_sizes']['partners'], 1)
        self.assertContains(response, 'Partners')
        self.assertEqual(response.context['unread_notification_count'], 1)

    def test_permission_roles_for_list_detail_decision_and_financial_actions(self):
        company = make_company('Pending company', status='pending')
        nonstaff = get_user_model().objects.create_user('nonstaff')
        nonstaff.groups.add(Group.objects.get(name=PARTNERS))
        for user in (self.support, self.customer, nonstaff):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('dashboard:partners')).status_code, 403)
            self.assertEqual(self.client.get(reverse('dashboard:partner_detail', args=[company.pk])).status_code, 403)
            self.assertEqual(self.client.post(reverse('dashboard:partner_decide', args=[company.pk]),
                {'decision':'approve'}).status_code, 403)
            with self.assertRaises(PermissionDenied):
                decide_company(company.pk, actor=user, decision='approve')
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(reverse('dashboard:partners')).status_code, 200)
        self.assertContains(self.client.get(reverse('dashboard:partner_detail', args=[company.pk])), company.email)
        for decision in ('verify', 'suspend', 'unsuspend'):
            with self.assertRaises(PermissionDenied):
                decide_company(company.pk, actor=self.reviewer, decision=decision, reason='Unauthorized')
        self.assertEqual(self.client.get(reverse('admin:partners_invoice_changelist')).status_code, 403)

    def test_staff_decision_audit_notification_and_repeat_protection(self):
        company = register_company(self.data(), applicant=self.customer)
        self.client.force_login(self.reviewer)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('dashboard:partner_decide', args=[company.pk]),
                {'decision':'approve', 'reason':'Documents checked'})
        self.assertRedirects(response, reverse('dashboard:partner_detail', args=[company.pk]))
        company.refresh_from_db()
        self.assertEqual(company.decided_by, self.reviewer)
        self.assertIsNotNone(company.decided_at)
        self.assertEqual(company.decision_reason, 'Documents checked')
        self.assertTrue(self.customer.groups.filter(name=ROLE_NAME).exists())
        self.assertTrue(PartnerAuditLog.objects.filter(company=company, actor=self.reviewer, action='company.approve').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.customer, message__contains='Documents checked').exists())
        self.assertEqual(mail.outbox[-1].to, [self.customer.email])
        self.assertIn('existing customer account', mail.outbox[-1].body)
        self.assertNotIn('Partner Company Login', mail.outbox[-1].body)
        count = Notification.objects.count()
        with self.assertRaisesMessage(ValidationError, 'cannot be repeated'):
            decide_company(company.pk, actor=self.reviewer, decision='approve')
        with self.assertRaises(ValidationError):
            decide_company(company.pk, actor=self.owner, decision='reject', reason='Second decision')
        self.assertEqual(Notification.objects.count(), count)
        self.client.force_login(self.owner)
        self.client.post(reverse('admin:partners_companyprofile_changelist'),
            {'action':'approve', '_selected_action':[str(company.pk)]})
        self.assertEqual(PartnerAuditLog.objects.filter(company=company, action='company.approve').count(), 1)

    def test_rejection_reason_required_and_resubmit_clears_decision_metadata(self):
        company = register_company(self.data(), applicant=self.customer)
        self.client.force_login(self.reviewer)
        url = reverse('dashboard:partner_decide', args=[company.pk])
        self.assertContains(self.client.post(url, {'decision':'reject', 'reason':' '}),
                            'A rejection reason is required.', status_code=400)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, {'decision':'reject', 'reason':'Provide a clearer document'})
        company.refresh_from_db()
        self.assertEqual(company.status, 'rejected')
        self.assertFalse(self.customer.groups.filter(name=ROLE_NAME).exists())
        self.assertIn('Provide a clearer document', mail.outbox[-1].body)
        self.assertTrue(Notification.objects.filter(recipient=self.customer, message__contains='Provide a clearer document').exists())
        register_company(self.data(), applicant=self.customer)
        company.refresh_from_db()
        self.assertEqual(company.status, 'pending')
        self.assertIsNone(company.decided_by)
        self.assertIsNone(company.decided_at)
        self.assertEqual(CompanyProfile.objects.filter(user=self.customer).count(), 1)

    def test_oldest_pending_first_search_status_and_csrf(self):
        first = make_company('First farm', status='pending')
        second = make_company('Second farm', status='pending')
        approved = make_company('Approved farm')
        CompanyProfile.objects.filter(pk=second.pk).update(submitted_at=timezone.now() - timedelta(days=2))
        self.client.force_login(self.reviewer)
        response = self.client.get(reverse('dashboard:partners'))
        self.assertEqual([item.pk for item in response.context['page_obj']], [second.pk, first.pk])
        response = self.client.get(reverse('dashboard:partners'), {'status':'approved', 'q':'Approved'})
        self.assertEqual([item.pk for item in response.context['page_obj']], [approved.pk])
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.reviewer)
        self.assertEqual(client.post(reverse('dashboard:partner_decide', args=[first.pk]), {'decision':'approve'}).status_code, 403)

    def test_rollback_does_not_notify_and_missing_smtp_logs_without_failing(self):
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    register_company(self.data(), applicant=self.customer)
                    raise RuntimeError('Rollback test')
        self.assertFalse(Notification.objects.exists())
        self.assertFalse(CompanyProfile.objects.exists())
        self.assertEqual(len(mail.outbox), 0)
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD=''):
            with self.assertLogs('partners.services', level='WARNING'):
                with self.captureOnCommitCallbacks(execute=True):
                    company = register_company(self.data(), applicant=self.customer)
        self.assertTrue(CompanyProfile.objects.filter(pk=company.pk).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.reviewer).exists())

    def test_delivery_failure_does_not_undo_application(self):
        self.client.force_login(self.customer)
        with patch('partners.services.EmailMessage.send', side_effect=OSError('Simulated mail outage')):
            with self.assertLogs('partners.services', level='ERROR'):
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(reverse('partners:apply'), self.data())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CompanyProfile.objects.filter(user=self.customer).exists())

    def test_notification_ownership_post_only_mark_read_and_unread_count(self):
        mine = Notification.objects.create(recipient=self.customer, message='Private customer notice', link='/partners/application/')
        other = Notification.objects.create(recipient=self.reviewer, message='Private staff notice')
        self.client.force_login(self.customer)
        response = self.client.get(reverse('notifications:inbox'))
        self.assertContains(response, mine.message)
        self.assertNotContains(response, other.message)
        self.assertEqual(response.context['unread_notification_count'], 1)
        self.assertEqual(self.client.get(reverse('notifications:mark_read', args=[mine.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse('notifications:mark_read', args=[other.pk])).status_code, 404)
        self.client.post(reverse('notifications:mark_read', args=[mine.pk]))
        self.assertEqual(self.client.get(reverse('notifications:inbox')).context['unread_notification_count'], 0)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        self.assertEqual(client.post(reverse('notifications:mark_read', args=[mine.pk])).status_code, 403)

    def test_only_applicant_partners_staff_and_owner_can_download_license(self):
        field = CompanyProfile._meta.get_field('trade_license_document')
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            with patch.object(field, 'storage', PartnerPrivateStorage()):
                self.client.force_login(self.customer)
                self.client.post(reverse('partners:apply'), {**self.data(), 'trade_license_document':
                    SimpleUploadedFile('license.pdf', b'%PDF-1.4\nDemo license', content_type='application/pdf')})
                company = CompanyProfile.objects.get(user=self.customer)
                url = reverse('partners:trade_license_download', args=[company.pk])
                for user in (self.customer, self.reviewer, self.owner):
                    self.client.force_login(user)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
                self.assertEqual(self.client.get(reverse('admin:partners_companyprofile_change', args=[company.pk])).status_code, 200)
                self.client.force_login(self.support)
                self.assertEqual(self.client.get(url).status_code, 403)
