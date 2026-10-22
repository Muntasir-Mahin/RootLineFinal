from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from partners.models import CompanyProduct
from products.models import Product
from .helpers import make_company, make_product


class PartnerStoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company()
        cls.product = make_product(cls.company)
        cls.buyer = get_user_model().objects.create_user('store-buyer', password='Buyer-demo-732!')

    def test_partner_products_never_enter_existing_marketplace_search_or_cart_models(self):
        regular = Product.objects.create(seller=self.company.user, name='Ordinary rice', category='Grain',
            price='80', stock_quantity=5, verification_status='verified')
        response = self.client.get(reverse('marketplace'))
        self.assertContains(response, regular.name)
        self.assertNotContains(response, self.product.name)
        response = self.client.get(reverse('site_search'), {'q': self.product.name})
        self.assertEqual(response.context['product_page'].paginator.count, 0)
        from orders.models import CartItem, OrderItem
        self.assertIs(CartItem._meta.get_field('product').related_model, Product)
        self.assertIs(OrderItem._meta.get_field('product').related_model, Product)

    def test_public_directory_store_and_product_visibility(self):
        self.assertContains(self.client.get(reverse('partners:directory')), self.company.name)
        self.assertEqual(self.client.get(self.company.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 200)
        for changes in [dict(status='pending'), dict(is_suspended=True), dict(is_active=False)]:
            with self.subTest(changes=changes):
                original = {name:getattr(self.company, name) for name in changes}
                for name, value in changes.items():
                    setattr(self.company, name, value)
                self.company.save()
                self.assertEqual(self.client.get(self.company.get_absolute_url()).status_code, 404)
                self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)
                self.assertNotContains(self.client.get(reverse('partners:directory')), self.company.name)
                for name, value in original.items():
                    setattr(self.company, name, value)
                self.company.save()
        self.product.is_active = False
        self.product.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)

    def test_contact_details_are_never_rendered_to_anonymous_visitors(self):
        for url in [self.company.get_absolute_url(), self.product.get_absolute_url()]:
            response = self.client.get(url)
            self.assertContains(response, 'Log in to view contact details')
            for value in [self.company.email, self.company.phone, self.company.address]:
                self.assertNotContains(response, value)
        self.client.force_login(self.buyer)
        response = self.client.get(self.company.get_absolute_url())
        for value in [self.company.email, self.company.phone, self.company.address]:
            self.assertContains(response, value)

    def test_pending_company_cannot_publish_and_other_company_products_are_404(self):
        pending = make_company('Pending farm', status='pending')
        self.client.force_login(pending.user)
        self.assertEqual(self.client.get(reverse('partners:product_add')).status_code, 403)
        self.client.force_login(self.company.user)
        other = make_company('Other Farm')
        product = make_product(other)
        for route in ['product_edit', 'product_delete', 'product_toggle', 'product_images']:
            self.assertEqual(self.client.post(reverse('partners:' + route, args=[product.pk]), {}).status_code, 404)
        self.assertTrue(CompanyProduct.objects.filter(pk=product.pk).exists())

    def test_company_can_add_hide_and_unhide_a_product(self):
        self.client.force_login(self.company.user)
        data = dict(name='New partner product', category=self.product.category_id, price='150',
            discount_price='125', unit='kg', stock_quantity='20', description='Fresh seed.', is_active='on')
        self.assertRedirects(self.client.post(reverse('partners:product_add'), data), reverse('partners:product_list'))
        product = CompanyProduct.objects.get(name='New partner product')
        self.assertEqual(product.sale_price, 125)
        self.client.post(reverse('partners:product_toggle', args=[product.pk]))
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 404)
        self.client.post(reverse('partners:product_toggle', args=[product.pk]))
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 200)

    def test_store_search_discount_sort_and_pagination_keep_filters(self):
        for index in range(13):
            make_product(self.company, name=f'Bulk seed {index}', price=str(200+index))
        discounted = make_product(self.company, name='Bulk seed special', price='500', discount_price='10')
        response = self.client.get(self.company.get_absolute_url(), {'q':'Bulk seed', 'sort':'price_low'})
        self.assertEqual(response.context['page'][0], discounted)
        self.assertEqual(len(response.context['page']), 12)
        self.assertContains(response, 'page=2')
        self.assertContains(response, 'sort=price_low')
        self.assertNotContains(response, '??')
