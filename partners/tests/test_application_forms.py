from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from partners.models import CustomerEmailVerification


class ApplicationFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('customer', email='customer@example.com')
        CustomerEmailVerification.objects.create(user=cls.user, email=cls.user.email, verified_at=timezone.now())

    def test_terms_link_next_to_required_unchecked_checkbox(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('partners:apply'))
        content = response.content.decode()
        self.assertContains(response, 'target="_blank" rel="noopener noreferrer"')
        self.assertContains(response, '(opens in a new tab)')
        checkbox = content[content.index('type="checkbox"'):content.index('>', content.index('type="checkbox"'))]
        self.assertNotIn('checked', checkbox)
        self.assertIn('required', checkbox)
        self.assertRegex(content, r'id_agree_terms[^\n]+Read Partner Terms')
        self.assertNotContains(response, 'type="password"')
        self.assertFalse(response.context['form'].is_bound)

    def test_terms_back_allows_internal_paths_and_rejects_external_urls(self):
        url = reverse('partners:terms')
        for bad in ('https://evil.example', '//evil.example', '/\\evil.example', 'javascript:alert(1)', '\n//evil.example'):
            with self.subTest(next=bad):
                response = self.client.get(url, {'next':bad})
                self.assertEqual(response.context['back_url'], reverse('partners:apply'))
        response = self.client.get(url, {'next':'/partners/apply/?section=company'})
        self.assertEqual(response.context['back_url'], '/partners/apply/?section=company')
        self.assertContains(response, 'Back to application')

    def test_failed_submission_keeps_entered_values_and_does_not_clear_draft(self):
        self.client.force_login(self.user)
        values = {'company_name':'Draft Farm', 'email':'business@example.com', 'phone':'01712345678',
            'address':'Private address', 'district':'Dhaka', 'division':'Dhaka', 'trade_license':'PRIVATE-123'}
        response = self.client.post(reverse('partners:apply'), values)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].is_bound)
        for name, value in values.items():
            self.assertEqual(response.context['form'][name].value(), value)
        self.assertNotIn('partner_application_submitted', self.client.session)
        self.assertContains(response, 'data-bound="true"')

    def test_success_sends_one_time_server_marker_to_clear_account_scoped_draft(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('partners:apply'), {'company_name':'Submitted farm',
            'email':'business@example.com', 'phone':'01712345678', 'address':'Dhaka',
            'district':'Dhaka', 'division':'Dhaka', 'agree_terms':'on'}, follow=True)
        self.assertContains(response, f'data-partner-draft-clear="rootline.partner-application:{self.user.pk}"')
        self.assertNotContains(self.client.get(reverse('partners:application_status')), 'data-partner-draft-clear')
