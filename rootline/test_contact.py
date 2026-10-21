from datetime import datetime, timezone as dt_timezone
from urllib.parse import parse_qs, unquote, urlsplit

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .contact import availability, contact_details, phone_number

CONTACT_EMPTY = {f'ROOTLINE_CONTACT_{key}': '' for key in [
    'BUSINESS_NAME', 'PHONE', 'WHATSAPP', 'EMAIL', 'FACEBOOK', 'MESSENGER', 'INSTAGRAM',
    'YOUTUBE', 'SOCIALS', 'ADDRESS', 'HOURS', 'LANGUAGES', 'REPLY_TIME', 'WHATSAPP_MESSAGE', 'EMAIL_SUBJECT',
]}


@override_settings(**CONTACT_EMPTY)
class ContactConfigurationTests(SimpleTestCase):
    def test_phone_normalisation_and_bad_values(self):
        for number in ['01923194036', '+880 1923-194036', '8801923194036', '008801923194036']:
            self.assertEqual(phone_number(number), ('+880 1923-194036', '+8801923194036'))
        for number in ['', 'not a phone', 'javascript:alert(1)', '+12', '01923194036?x=1', '+880١٩٢٣١٩٤٠٣٦']:
            self.assertEqual(phone_number(number), ('', ''))

    def test_links_encode_text_and_legacy_email_works(self):
        from .context_processors import site_contact
        with override_settings(ROOTLINE_CONTACT_PHONE='01923194036', ROOTLINE_CONTACT_WHATSAPP='+8801923194036',
                               ROOTLINE_CONTACT_EMAIL='support@example.test',
                               ROOTLINE_CONTACT_WHATSAPP_MESSAGE='বাংলা help & order #1?',
                               ROOTLINE_CONTACT_EMAIL_SUBJECT='Payment & order #1'):
            contact = contact_details()
            self.assertEqual(contact['phone_href'], 'tel:+8801923194036')
            whatsapp = urlsplit(contact['whatsapp_href'])
            self.assertEqual(whatsapp.netloc, 'wa.me')
            self.assertEqual(whatsapp.path, '/8801923194036')
            self.assertEqual(parse_qs(whatsapp.query), {'text':['বাংলা help & order #1?']})
            self.assertEqual(parse_qs(urlsplit(contact['email_href']).query), {'subject':['Payment & order #1']})
            self.assertEqual(site_contact(None)['contact_email'], 'support@example.test')

    def test_email_local_part_cannot_turn_into_a_query_parameter(self):
        with override_settings(ROOTLINE_CONTACT_EMAIL='help?team@example.test'):
            link = urlsplit(contact_details()['email_href'])
            self.assertEqual(unquote(link.path), 'help?team@example.test')
            self.assertEqual(parse_qs(link.query), {'subject':['RootLine support']})

    def test_invalid_links_hide_and_extra_socials_are_validated(self):
        with override_settings(ROOTLINE_CONTACT_FACEBOOK='javascript:alert(1)',
                               ROOTLINE_CONTACT_MESSENGER='https://user:password@example.com',
                               ROOTLINE_CONTACT_EMAIL='bad\r\nBcc:bad@example.com',
                               ROOTLINE_CONTACT_SOCIALS='[{"label":"Community","url":"https://example.com/community"},{"label":"","url":"https://example.com"},{"label":"bad","url":"data:text/html,no"}]'):
            contact = contact_details()
            self.assertEqual([c['key'] for c in contact['channels']], ['social'])
            self.assertEqual(contact['socials'][0]['label'], 'Community')
            self.assertEqual(contact['email'], '')
        for malformed in ['not json', '{}', '[null,4,"text"]']:
            with override_settings(ROOTLINE_CONTACT_SOCIALS=malformed):
                self.assertEqual(contact_details()['channels'], [])

    def test_empty_configuration_has_no_hours_claim_or_channels(self):
        contact = contact_details()
        self.assertFalse(contact['has_channels'])
        self.assertEqual(contact['phone_href'], '')
        self.assertEqual(contact['whatsapp_href'], '')
        self.assertIsNone(contact['availability'])

    def test_schedule_uses_dhaka_boundaries_and_weekend(self):
        hours = 'Sat-Thu, 9:00 AM - 8:00 PM (Bangladesh time)'
        self.assertTrue(availability(hours, datetime(2026,10,22,3,0,tzinfo=dt_timezone.utc))['is_open'])
        closed = availability(hours, datetime(2026,10,22,14,0,tzinfo=dt_timezone.utc))
        self.assertFalse(closed['is_open'])
        self.assertEqual(closed['label'], 'Back Sat at 9:00 AM')
        self.assertEqual(closed['next_open'], '2026-10-24T09:00:00+06:00')
        before = availability(hours, datetime(2026,10,24,2,59,tzinfo=dt_timezone.utc))
        self.assertEqual(before['label'], 'Back at 9:00 AM')
        friday = availability(hours, datetime(2026,10,23,4,0,tzinfo=dt_timezone.utc))
        self.assertEqual(friday['label'], 'Back tomorrow at 9:00 AM')

    def test_overnight_schedule_and_unknown_text(self):
        # Friday's overnight shift is still open on Saturday at 01:00 Dhaka.
        self.assertTrue(availability('Fri, 9:00 PM - 2:00 AM', datetime(2026,10,23,19,0,tzinfo=dt_timezone.utc))['is_open'])
        for text in ['', 'e.g. Sat-Thu, 9:00 AM - 8:00 PM', 'Call any time', 'Mon, 25:00 AM - 8:00 PM', 'Daily, 9:00 AM - 9:00 AM']:
            self.assertIsNone(availability(text))
        self.assertTrue(availability('Daily, 9:00 AM - 8:00 PM', datetime(2026,10,22,5,0,tzinfo=dt_timezone.utc))['is_open'])


@override_settings(**CONTACT_EMPTY)
class ContactPageTests(TestCase):
    def test_empty_page_and_sheet_have_only_real_support_destinations(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We're here to help")
        self.assertContains(response, 'Find answers in our FAQ')
        self.assertNotContains(response, 'wa.me/')
        self.assertNotContains(response, 'mailto:')
        self.assertNotContains(response, 'tel:')
        self.assertNotContains(response, 'Available now')
        self.assertEqual(self.client.post(reverse('contact')).status_code, 405)

    def test_configured_channels_escape_text_and_secure_external_links(self):
        with override_settings(ROOTLINE_CONTACT_PHONE='01923194036', ROOTLINE_CONTACT_WHATSAPP='01923194036',
                               ROOTLINE_CONTACT_EMAIL='support@example.test', ROOTLINE_CONTACT_FACEBOOK='https://facebook.com/yourpage',
                               ROOTLINE_CONTACT_ADDRESS='<script>alert(1)</script>'):
            response = self.client.get(reverse('contact'))
            self.assertContains(response, 'tel:+8801923194036')
            self.assertContains(response, 'https://wa.me/8801923194036?text=')
            self.assertContains(response, 'mailto:support@example.test?subject=')
            self.assertContains(response, 'target="_blank" rel="noopener noreferrer"')
            self.assertNotContains(response, '<script>alert(1)</script>')
            self.assertContains(response, '&lt;script&gt;')
            self.assertContains(self.client.get(reverse('help')), 'Chat on WhatsApp')

    def test_order_links_include_only_encoded_order_number_and_forms_remain(self):
        from django.template.loader import render_to_string
        with override_settings(ROOTLINE_CONTACT_PHONE='01923194036', ROOTLINE_CONTACT_WHATSAPP='01923194036',
                               ROOTLINE_CONTACT_EMAIL='support@example.test'):
            html = render_to_string('components/order_contact.html', {'contact':contact_details(), 'order_id':42})
            self.assertIn('Order%20%2342', html)
            self.assertIn('Need help with order #42?', html)
            self.assertNotIn('recipient_name', html)
            self.assertNotIn('<form', html)
