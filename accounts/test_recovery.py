import re
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountRecoveryTests(TestCase):
    message = 'If an account with that email exists, we have sent an email.'

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='recovery-buyer', email='Buyer@example.com', password='Original-harvest-782!',
        )

    def setUp(self):
        cache.clear()

    def reset_link(self):
        return urlsplit(re.search(r'https?://\S+', mail.outbox[0].body).group()).path

    def public_body(self, response):
        # CSRF masks are intentionally randomized on every render.
        return re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]+(\")',
                      r'\1TOKEN\2', response.content.decode())

    def test_login_links_and_existing_login_still_work(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, f'href="{reverse("password_reset")}"')
        self.assertContains(response, f'href="{reverse("username_recovery")}"')
        self.assertRedirects(self.client.post(reverse('login'), {
            'username': self.user.get_username(), 'password': 'Original-harvest-782!',
        }), reverse('profile'))

    def test_password_reset_flow_case_insensitive_and_single_use(self):
        response = self.client.post(reverse('password_reset'), {'email': 'BUYER@EXAMPLE.COM'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['Buyer@example.com'])
        self.assertEqual(mail.outbox[0].subject, 'Reset your RootLine password')
        link = self.reset_link()
        response = self.client.get(link)
        self.assertEqual(response.status_code, 302)
        form_url = response.url
        self.assertContains(self.client.get(form_url), 'Save new password')
        response = self.client.post(form_url, {
            'new_password1': 'New-harvest-recovery-972!',
            'new_password2': 'New-harvest-recovery-972!',
        })
        self.assertRedirects(response, reverse('password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('New-harvest-recovery-972!'))
        self.assertFalse(self.user.check_password('Original-harvest-782!'))
        self.assertFalse(Client().get(link).context['validlink'])
        self.assertRedirects(self.client.post(reverse('login'), {
            'username': self.user.get_username(), 'password': 'New-harvest-recovery-972!',
        }), reverse('profile'))

    def test_expired_password_reset_link_is_rejected(self):
        expired = datetime.now() - timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 1)
        with patch.object(default_token_generator, '_now', return_value=expired):
            self.client.post(reverse('password_reset'), {'email': self.user.email})
        response = self.client.get(self.reset_link())
        self.assertFalse(response.context['validlink'])
        self.assertContains(response, 'invalid or expired')

    def test_shared_email_password_reset_sends_one_link_per_active_usable_account(self):
        User = get_user_model()
        User.objects.create_user('second-buyer', email='buyer@example.com', password='Another-harvest-782!')
        User.objects.create_user('inactive-buyer', email='buyer@example.com', is_active=False,
                                 password='Another-harvest-782!')
        User.objects.create_user('unusable-buyer', email='buyer@example.com', password=None)
        self.client.post(reverse('password_reset'), {'email': 'buyer@example.com'})
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('recovery-buyer', mail.outbox[0].body + mail.outbox[1].body)
        self.assertIn('second-buyer', mail.outbox[0].body + mail.outbox[1].body)
        self.assertNotIn('inactive-buyer', mail.outbox[0].body + mail.outbox[1].body)
        self.assertNotEqual(mail.outbox[0].body, mail.outbox[1].body)

    def test_username_recovery_lists_all_active_accounts_case_insensitively(self):
        User = get_user_model()
        User.objects.create_user('second-buyer', email='buyer@example.com')
        User.objects.create_user('inactive-buyer', email='buyer@example.com', is_active=False)
        response = self.client.post(reverse('username_recovery'), {'email': 'BUYER@EXAMPLE.COM'})
        self.assertRedirects(response, reverse('username_recovery_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['Buyer@example.com'])
        self.assertIn('- recovery-buyer', mail.outbox[0].body)
        self.assertIn('- second-buyer', mail.outbox[0].body)
        self.assertNotIn('inactive-buyer', mail.outbox[0].body)
        self.assertIn('http://testserver/login/', mail.outbox[0].body)

    def test_unknown_emails_get_the_same_public_response(self):
        for route in ['password_reset', 'username_recovery']:
            with self.subTest(route=route):
                known = self.client.post(reverse(route), {'email': self.user.email}, follow=True)
                mail_count = len(mail.outbox)
                unknown = self.client.post(reverse(route), {'email': 'missing@example.com'}, follow=True)
                self.assertEqual(len(mail.outbox), mail_count)
                self.assertEqual(known.redirect_chain, unknown.redirect_chain)
                self.assertContains(known, self.message)
                self.assertContains(unknown, self.message)
                self.assertEqual(self.public_body(known), self.public_body(unknown))
                self.assertNotContains(known, self.user.get_username())

    def test_inactive_accounts_receive_no_recovery_email(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        for route in ['password_reset', 'username_recovery']:
            response = self.client.post(reverse(route), {'email': self.user.email}, follow=True)
            self.assertContains(response, self.message)
        self.assertEqual(len(mail.outbox), 0)

    def test_recovery_forms_require_csrf_and_validate_email(self):
        client = Client(enforce_csrf_checks=True)
        for route in ['password_reset', 'username_recovery']:
            with self.subTest(route=route):
                self.assertEqual(client.post(reverse(route), {'email': self.user.email}).status_code, 403)
                response = client.get(reverse(route))
                self.assertContains(response, 'name="csrfmiddlewaretoken"')
                response = client.post(reverse(route), {
                    'email': 'invalid', 'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
                })
                self.assertEqual(response.status_code, 200)
                self.assertIn('email', response.context['form'].errors)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_throttle_is_case_insensitive_and_shared_by_both_features(self):
        for route in ['username_recovery', 'password_reset', 'username_recovery']:
            self.client.post(reverse(route), {'email': self.user.email})
        self.assertEqual(len(mail.outbox), 3)
        response = self.client.post(reverse('password_reset'), {'email': self.user.email.upper()},
                                    REMOTE_ADDR='192.0.2.4', follow=True)
        self.assertContains(response, self.message)
        self.assertEqual(len(mail.outbox), 3)

    def test_ip_throttle_cannot_be_bypassed_with_different_emails_or_forwarded_header(self):
        for index in range(10):
            self.client.post(reverse('username_recovery'), {'email': f'unknown-{index}@example.com'})
        response = self.client.post(reverse('password_reset'), {'email': self.user.email},
                                    HTTP_X_FORWARDED_FOR='192.0.2.9', follow=True)
        self.assertContains(response, self.message)
        self.assertEqual(len(mail.outbox), 0)

    def test_username_delivery_failure_keeps_the_generic_response(self):
        with patch('accounts.recovery_views.EmailMessage.send', side_effect=OSError('SMTP unavailable')):
            with self.assertLogs('accounts.recovery_views', level='ERROR'):
                response = self.client.post(reverse('username_recovery'), {'email': self.user.email}, follow=True)
        self.assertContains(response, self.message)
        self.assertNotContains(response, 'SMTP unavailable')

    def test_password_delivery_failure_keeps_the_generic_response(self):
        with patch('django.contrib.auth.forms.EmailMultiAlternatives.send', side_effect=OSError('SMTP unavailable')):
            with self.assertLogs('django.contrib.auth', level='ERROR'):
                response = self.client.post(reverse('password_reset'), {'email': self.user.email}, follow=True)
        self.assertContains(response, self.message)
        self.assertNotContains(response, 'SMTP unavailable')

    def test_https_request_produces_an_https_reset_link(self):
        self.client.post(reverse('password_reset'), {'email': self.user.email}, secure=True)
        self.assertIn('https://testserver/password/reset/', mail.outbox[0].body)
