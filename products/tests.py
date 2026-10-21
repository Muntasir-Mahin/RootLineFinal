from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from .models import Product


def photo(name, color):
    buffer = BytesIO()
    Image.new('RGB', (64, 48), color).save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class SellerProductImageTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        override = override_settings(MEDIA_ROOT=media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.seller = User.objects.create_user('photo-seller', seller_approved=True)
        self.client.force_login(self.seller)
        self.product = Product.objects.create(
            seller=self.seller, name='Honey', description='A honey listing.', category='Honey',
            price=1000, stock_quantity=100, unit='kg', selling_type='fixed',
            image=photo('before.png', (204, 208, 207)),
        )
        self.data = {
            'name':'Honey', 'description':'Updated honey description.', 'category':'Honey',
            'price':'1000', 'stock_quantity':'100', 'unit':'kg', 'selling_type':'fixed',
            'is_available':'on',
        }

    def test_uploaded_replacement_is_saved_and_shown_on_seller_list_and_detail(self):
        replacement = photo('after.png', (37, 55, 69))
        expected = replacement.read()
        replacement.seek(0)
        response = self.client.post(reverse('edit_product', args=[self.product.pk]),
                                    {**self.data, 'image':replacement})
        self.assertRedirects(response, reverse('my_products'))
        self.product.refresh_from_db()
        self.assertTrue(self.product.image.name.startswith('products/after'))
        with self.product.image.open('rb') as saved:
            self.assertEqual(saved.read(), expected)
        for url in [reverse('my_products'), reverse('product_detail', args=[self.product.pk])]:
            response = self.client.get(url)
            self.assertContains(response, f'src="{self.product.image.url}"')
            self.assertContains(response, 'alt="Honey"')

    def test_text_only_edit_keeps_the_uploaded_photo(self):
        name = self.product.image.name
        response = self.client.post(reverse('edit_product', args=[self.product.pk]), self.data)
        self.assertRedirects(response, reverse('my_products'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, name)
        self.assertContains(self.client.get(reverse('my_products')), f'src="{self.product.image.url}"')

    def test_explicit_image_clear_uses_the_no_photo_placeholder(self):
        response = self.client.post(reverse('edit_product', args=[self.product.pk]),
                                    {**self.data, 'image-clear':'on'})
        self.assertRedirects(response, reverse('my_products'))
        self.product.refresh_from_db()
        self.assertFalse(self.product.image)
        self.assertContains(self.client.get(reverse('my_products')), 'No photo uploaded')
