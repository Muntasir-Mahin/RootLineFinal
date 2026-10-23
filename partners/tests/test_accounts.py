import io

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from partners.forms import CompanyProfileForm
from partners.models import Achievement, CompanyProfile, GalleryImage, PartnerAuditLog
from partners.services import decide_company
from .helpers import make_company


class PartnerAccountTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_dashboard_rejects_normal_user_and_profile_cannot_self_approve(self):
        buyer = get_user_model().objects.create_user('buyer')
        self.client.force_login(buyer)
        self.assertEqual(self.client.get(reverse('partners:dashboard')).status_code, 403)
        company = make_company(status='pending')
        self.client.force_login(company.user)
        data = dict(name=company.name, email=company.email, phone=company.phone, address=company.address,
            district=company.district, division=company.division, status='approved', is_verified='on')
        self.assertEqual(self.client.post(reverse('partners:profile_edit'), data).status_code, 403)
        company.refresh_from_db()
        self.assertEqual(company.status, 'pending')
        self.assertFalse(company.is_verified)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_approval_and_rejection_require_owner_and_audit_and_notify(self):
        company = make_company(status='pending')
        owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-demo-942!')
        with self.assertRaises(PermissionDenied):
            decide_company(company.pk, actor=company.user, decision='approve')
        with self.captureOnCommitCallbacks(execute=True):
            decide_company(company.pk, actor=owner, decision='approve')
        company.refresh_from_db()
        self.assertTrue(company.can_publish)
        self.assertEqual(len(mail.outbox), 1)
        with self.assertRaises(ValidationError):
            decide_company(company.pk, actor=owner, decision='reject')
        decide_company(company.pk, actor=owner, decision='reject', reason='Trade license needs clarification.')
        self.assertTrue(PartnerAuditLog.objects.filter(company=company, action='company.reject').exists())

    def test_asset_ownership_and_csrf_are_enforced(self):
        first = make_company()
        other = make_company('Other Farm')
        achievement = Achievement.objects.create(company=other, title='Other award', year=2025)
        self.client.force_login(first.user)
        for route in ['partners:asset_edit', 'partners:asset_delete']:
            self.assertEqual(self.client.post(reverse(route, args=['achievements', achievement.pk]), {}).status_code, 404)
        client = Client(enforce_csrf_checks=True)
        client.force_login(first.user)
        self.assertEqual(client.post(reverse('partners:profile_edit'), {}).status_code, 403)

    def test_image_validation_and_gallery_limit(self):
        company = make_company()
        form = CompanyProfileForm(data=dict(name=company.name, email=company.email, phone=company.phone,
            address=company.address, district=company.district, division=company.division),
            files={'logo': SimpleUploadedFile('evil.svg', b'<svg onload="alert(1)"/>', content_type='image/svg+xml')},
            instance=company)
        self.assertFalse(form.is_valid())
        self.assertIn('logo', form.errors)
        for index in range(12):
            GalleryImage.objects.create(company=company, image=f'partners/gallery/fixture-{index}.jpg')
        extra = GalleryImage(company=company, image='partners/gallery/extra.jpg')
        with self.assertRaises(ValidationError):
            extra.clean()

    def test_new_admin_pages_work_for_owner_only(self):
        company = make_company()
        owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-demo-942!')
        self.client.force_login(owner)
        self.assertEqual(self.client.get(reverse('admin:partners_companyprofile_change', args=[company.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:partners_achievement_add')).status_code, 200)
        self.client.force_login(company.user)
        self.assertEqual(self.client.get(reverse('admin:partners_companyprofile_changelist')).status_code, 403)
