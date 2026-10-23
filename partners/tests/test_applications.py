import re
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail, signing
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from partners.email_verification import MAX_AGE, SALT, confirm_verification, is_verified, send_verification
from partners.models import CompanyProfile, CustomerEmailVerification
from partners.services import ROLE_NAME, decide_company, register_company
from partners.storage import PartnerPrivateStorage
from .helpers import make_company


class PartnerApplicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('customer', email='customer@example.com', password='Customer-test-394!')
        CustomerEmailVerification.objects.create(user=cls.user, email=cls.user.email, verified_at=timezone.now())
        cls.owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-test-846!')

    def setUp(self):
        cache.clear()

    def data(self, **kwargs):
        values = dict(company_name='Customer Agro', email='company@example.com', phone='01700000001',
            address='Dhaka', district='Dhaka', division='Dhaka', trade_license='DEMO-123', agree_terms='on')
        values.update(kwargs)
        return values

    def test_anonymous_redirect_and_signup_guidance_and_old_urls(self):
        url = reverse('partners:apply')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.redirect_chain[0][0], reverse('login') + '?next=' + url)
        self.assertContains(response, 'Create a customer account first, then apply for partnership')
        self.assertContains(response, reverse('register') + '?next=')
        self.assertRedirects(self.client.post(reverse('partners:register'), self.data()), url,
                             fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('partners:login')).status_code, 302)
        self.assertFalse(CompanyProfile.objects.exists())

    def test_application_never_creates_user_or_changes_credentials_and_needs_terms(self):
        self.client.force_login(self.user)
        count = get_user_model().objects.count()
        response = self.client.get(reverse('partners:apply'))
        self.assertNotContains(response, 'type="password"')
        self.assertEqual(self.client.post(reverse('partners:apply'), self.data(agree_terms='')).status_code, 200)
        self.assertFalse(CompanyProfile.objects.exists())
        self.assertRedirects(self.client.post(reverse('partners:apply'), self.data()), reverse('partners:application_status'))
        company = CompanyProfile.objects.get()
        self.assertEqual(company.user_id, self.user.pk)
        self.assertEqual(company.status, 'pending')
        self.assertFalse(self.user.groups.filter(name=ROLE_NAME).exists())
        self.assertEqual(get_user_model().objects.count(), count)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'customer@example.com')
        self.assertTrue(self.user.check_password('Customer-test-394!'))
        self.assertContains(self.client.get(reverse('profile')), 'Pending')

    def test_one_application_eligibility_and_rejected_resubmission(self):
        company = register_company(self.data(), applicant=self.user)
        self.client.force_login(self.user)
        self.assertRedirects(self.client.post(reverse('partners:apply'), self.data()), reverse('partners:application_status'))
        with self.assertRaises(ValidationError):
            register_company(self.data(), applicant=self.user)
        decide_company(company.pk, actor=self.owner, decision='reject', reason='Update the address')
        self.assertContains(self.client.get(reverse('partners:application_status')), 'Update the address')
        self.assertRedirects(self.client.post(reverse('partners:apply'), self.data(address='Updated address')),
                             reverse('partners:application_status'))
        company.refresh_from_db()
        self.assertEqual(company.address, 'Updated address')
        self.assertEqual(company.status, 'pending')
        self.assertEqual(company.rejection_reason, '')
        self.assertEqual(CompanyProfile.objects.count(), 1)
        decide_company(company.pk, actor=self.owner, decision='approve')
        self.assertRedirects(self.client.get(reverse('partners:apply')), reverse('partners:application_status'))
        self.assertContains(self.client.get(reverse('profile')), 'Partner Dashboard')

    def test_staff_and_superusers_cannot_apply_and_other_applications_are_private(self):
        staff = get_user_model().objects.create_user('staff', is_staff=True)
        for user in (staff, self.owner):
            self.client.force_login(user)
            response = self.client.post(reverse('partners:apply'), self.data(), follow=True)
            self.assertContains(response, 'Staff and superuser accounts cannot apply')
            with self.assertRaises(PermissionDenied):
                register_company(self.data(), applicant=user)
        other = make_company('Private company', status='rejected')
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get(reverse('partners:application_status'), follow=True), other.name)

    def test_duplicate_name_is_explicit_but_duplicate_email_is_generic(self):
        other = make_company('Existing name', email='used@example.com')
        self.client.force_login(self.user)
        response = self.client.post(reverse('partners:apply'), self.data(company_name='EXISTING NAME'))
        self.assertContains(response, 'A company with this name already exists.')
        response = self.client.post(reverse('partners:apply'), self.data(email='USED@EXAMPLE.COM'))
        self.assertContains(response, 'We could not submit this application with these details.')
        self.assertNotContains(response, 'email already')
        self.assertEqual(CompanyProfile.objects.count(), 1)

    def test_approval_suspension_preserve_customer_and_business_email_is_separate(self):
        company = register_company(self.data(), applicant=self.user)
        decide_company(company.pk, actor=self.owner, decision='approve')
        self.assertTrue(self.user.groups.filter(name=ROLE_NAME).exists())
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('partners:dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('cart')).status_code, 200)
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)
        self.client.post(reverse('partners:profile_edit'), dict(name=company.name, email='new-business@example.com',
            phone=company.phone, address=company.address, district=company.district, division=company.division))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'customer@example.com')
        decide_company(company.pk, actor=self.owner, decision='suspend', reason='Owner review')
        self.assertFalse(self.user.groups.filter(name=ROLE_NAME).exists())
        self.assertEqual(self.client.get(reverse('partners:dashboard')).status_code, 403)
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)

    def test_private_license_validated_and_not_publicly_downloadable(self):
        self.client.force_login(self.user)
        field = CompanyProfile._meta.get_field('trade_license_document')
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            with patch.object(field, 'storage', PartnerPrivateStorage()):
                response = self.client.post(reverse('partners:apply'), self.data(trade_license_document=
                    SimpleUploadedFile('bad.svg', b'<svg onload="alert(1)"/>', content_type='image/svg+xml')))
                self.assertContains(response, 'valid JPG')
                self.assertFalse(CompanyProfile.objects.exists())
                self.client.post(reverse('partners:apply'), self.data(trade_license_document=
                    SimpleUploadedFile('license.pdf', b'%PDF-1.4\nDemo license', content_type='application/pdf')))
                company = CompanyProfile.objects.get()
                url = reverse('partners:trade_license_download', args=[company.pk])
                with self.assertRaises(ValueError):
                    _ = company.trade_license_document.url
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                b''.join(response.streaming_content)
                stranger = get_user_model().objects.create_user('stranger')
                self.client.force_login(stranger)
                self.assertEqual(self.client.get(url).status_code, 403)
                self.client.logout()
                self.assertEqual(self.client.get(url).status_code, 302)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_customer_email_verification_expiry_binding_replay_and_email_change(self):
        CustomerEmailVerification.objects.filter(user=self.user).delete()
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse('partners:apply')), reverse('partners:verify_email'))
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse('partners:verify_email'))
        self.assertEqual(mail.outbox[-1].to, [self.user.email])
        token = re.search(r'/partners/verify-email/([^\s/]+)/', mail.outbox[-1].body).group(1)
        url = reverse('partners:verify_email_confirm', args=[token])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(is_verified(self.user))
        other = get_user_model().objects.create_user('other', email=self.user.email)
        with self.assertRaises(ValidationError):
            confirm_verification(other, token)
        with patch('django.core.signing.time.time', return_value=__import__('time').time() + MAX_AGE + 10):
            with self.assertRaises(ValidationError):
                confirm_verification(self.user, token)
        self.assertRedirects(self.client.post(url), reverse('partners:apply'))
        self.assertTrue(is_verified(self.user))
        with self.assertRaises(ValidationError):
            confirm_verification(self.user, token)
        self.user.email = 'changed@example.com'
        self.user.save(update_fields=['email'])
        self.assertFalse(is_verified(self.user))

    def test_apply_csrf_normal_login_safe_next_and_legacy_email_login(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('partners:apply'), self.data()).status_code, 403)
        self.client.logout()
        self.assertRedirects(self.client.post(reverse('login') + '?next=https://evil.example',
            {'username':self.user.username, 'password':'Customer-test-394!'}), reverse('profile'))
        self.client.logout()
        self.assertRedirects(self.client.post(reverse('login') + '?next=/partners/apply/',
            {'username':self.user.username, 'password':'Customer-test-394!'}), reverse('partners:apply'))
        legacy = make_company('Legacy company')
        legacy.user.username = 'partner-' + 'a' * 32
        legacy.user.save(update_fields=['username'])
        self.client.logout()
        self.assertRedirects(self.client.post(reverse('login'), {'username':legacy.email, 'password':'Partner-demo-793!'}), reverse('profile'))
        legacy.user.refresh_from_db()
        self.assertEqual(legacy.user.username, 'partner-' + 'a' * 32)
