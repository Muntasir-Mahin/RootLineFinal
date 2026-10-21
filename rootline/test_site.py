from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from agro_updates.models import Video
from products.models import Product


class PublicSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller = User.objects.create_user('search-seller')
        cls.product = Product.objects.create(seller=cls.seller, name='Fresh rice',
            description='Organic harvest', category='Grain', price='80', stock_quantity='5',
            verification_status='verified')
        for values in [dict(name='Pending rice', verification_status='pending'),
                       dict(name='Removed rice', is_available=False),
                       dict(name='Sold rice', stock_quantity=0)]:
            data = dict(seller=cls.seller, name='Rice', description='Private crop', category='Grain',
                        verification_status='verified', stock_quantity=5)
            data.update(values)
            Product.objects.create(**data)
        cls.video = Video.objects.create(title='Growing rice', video_id='abcdefghijk',
            youtube_url='https://www.youtube.com/watch?v=abcdefghijk',
            is_published=True, published_at=timezone.now())
        Video.objects.create(title='Draft rice', video_id='lmnopqrstuv', is_published=False)
        Video.objects.create(title='Future rice', video_id='01234567890',
                             is_published=True, published_at=timezone.now()+timedelta(days=1))

    def test_search_only_returns_public_available_content(self):
        response = self.client.get(reverse('site_search'), {'q': 'rice'})
        self.assertContains(response, self.product.name)
        self.assertContains(response, self.video.title)
        for title in ['Pending rice', 'Removed rice', 'Sold rice', 'Draft rice', 'Future rice']:
            self.assertNotContains(response, title)
        self.assertEqual(response.context['product_page'].paginator.count, 1)
        self.assertEqual(response.context['video_page'].paginator.count, 1)

    def test_search_matches_descriptions_and_categories_and_bounds_query(self):
        for query in ['Organic', 'Grain']:
            response = self.client.get(reverse('site_search'), {'q': query})
            self.assertEqual(list(response.context['product_page']), [self.product])
        response = self.client.get(reverse('site_search'), {'q': 'x'*200})
        self.assertEqual(len(response.context['query']), 150)

    def test_empty_query_does_not_list_catalogue_and_markup_is_escaped(self):
        response = self.client.get(reverse('site_search'))
        self.assertEqual(response.context['product_page'].paginator.count, 0)
        response = self.client.get(reverse('site_search'), {'q': '<script>alert(1)</script>'})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_pagination_keeps_query_and_other_result_page(self):
        Product.objects.bulk_create([Product(seller=self.seller, name=f'Rice {i}', description='Crop',
            category='Grain', stock_quantity=1, verification_status='verified') for i in range(13)])
        response = self.client.get(reverse('site_search'), {'q': 'rice', 'videos_page': 1})
        self.assertEqual(len(response.context['product_page']), 12)
        self.assertContains(response, 'products_page=2&amp;videos_page=1')
        self.assertEqual(self.client.post(reverse('site_search')).status_code, 405)


class SiteFeedbackTests(TestCase):
    def test_login_errors_are_visible_without_claiming_success(self):
        response = self.client.post(reverse('login'), {'username': 'nobody', 'password': 'wrong'})
        self.assertContains(response, 'The username or password was not recognised.')
        self.assertNotContains(response, 'Your account was created.')

    def test_theme_update_requires_authentication_and_csrf(self):
        user = User.objects.create_user('theme-user', password='Theme-test-942!')
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('toggle_theme'), {'theme': 'dark'}).status_code, 403)
        client.force_login(user)
        response = client.get(reverse('profile'))
        token = client.cookies['csrftoken'].value
        self.assertContains(response, 'id="theme-toggle"')
        result = client.post(reverse('toggle_theme'), {'theme': 'dark', 'csrfmiddlewaretoken': token})
        self.assertEqual(result.json()['theme'], 'dark')
        user.refresh_from_db()
        self.assertEqual(user.theme_preference, 'dark')
        self.assertContains(client.get(reverse('profile')), 'data-account-theme="dark"')
        self.assertEqual(client.post(reverse('toggle_theme'), {'theme': 'invalid', 'csrfmiddlewaretoken': token}).status_code, 400)

    def test_help_and_optional_contact(self):
        response = self.client.get(reverse('help'))
        self.assertContains(response, '<details>')
        self.assertContains(response, 'Skip to content')
        self.assertNotContains(response, 'mailto:')
        with self.settings(ROOTLINE_CONTACT_EMAIL='support@example.com'):
            self.assertContains(self.client.get(reverse('help')), 'mailto:support@example.com')
