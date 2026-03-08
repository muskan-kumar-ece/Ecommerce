from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from products.models import Category, Product, ProductImage

from .models import Wishlist


class WishlistAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='wishlist-user@example.com',
            password='StrongPass123',
            name='Wishlist User',
        )
        self.other_user = get_user_model().objects.create_user(
            email='other-wishlist-user@example.com',
            password='StrongPass123',
            name='Other Wishlist User',
        )
        self.category = Category.objects.create(name='Accessories')
        self.product = Product.objects.create(
            category=self.category,
            name='Wireless Mouse',
            description='Ergonomic mouse',
            price=Decimal('1299.00'),
            sku='ACC-MOUSE-001',
            stock_quantity=20,
            is_refurbished=False,
            condition_grade='A',
            is_active=True,
        )
        ProductImage.objects.create(
            product=self.product,
            image_url='https://example.com/mouse.jpg',
            is_primary=True,
        )

    def test_wishlist_endpoints_require_authentication(self):
        list_response = self.client.get('/api/v1/wishlist/')
        add_response = self.client.post('/api/v1/wishlist/', {'product': self.product.id}, format='json')
        delete_response = self.client.delete(f'/api/v1/wishlist/{self.product.id}/')

        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(add_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(delete_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_and_list_wishlist_items(self):
        self.client.force_authenticate(user=self.user)

        add_response = self.client.post('/api/v1/wishlist/', {'product': self.product.id}, format='json')
        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(add_response.data['product'], self.product.id)
        self.assertEqual(add_response.data['product_name'], self.product.name)
        self.assertEqual(add_response.data['product_price'], '1299.00')
        self.assertEqual(add_response.data['image_url'], 'https://example.com/mouse.jpg')
        self.assertEqual(add_response.data['product_details']['slug'], self.product.slug)
        self.assertEqual(add_response.data['product_details']['image'], 'https://example.com/mouse.jpg')

        list_response = self.client.get('/api/v1/wishlist/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]['product'], self.product.id)

    def test_duplicate_wishlist_add_does_not_create_new_entry(self):
        self.client.force_authenticate(user=self.user)

        first_response = self.client.post('/api/v1/wishlist/', {'product': self.product.id}, format='json')
        second_response = self.client.post('/api/v1/wishlist/', {'product': self.product.id}, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Wishlist.objects.filter(user=self.user, product=self.product).count(), 1)

    def test_list_only_returns_authenticated_users_items(self):
        Wishlist.objects.create(user=self.other_user, product=self.product)
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/v1/wishlist/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_delete_wishlist_item(self):
        Wishlist.objects.create(user=self.user, product=self.product)
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(f'/api/v1/wishlist/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Wishlist.objects.filter(user=self.user, product=self.product).exists())

    def test_delete_nonexistent_item_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/v1/wishlist/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_wishlist_mutation_endpoints_are_rate_limited(self):
        cache.clear()
        original_rates = SimpleRateThrottle.THROTTLE_RATES.copy()
        SimpleRateThrottle.THROTTLE_RATES["wishlist_mutations"] = "2/minute"
        self.client.force_authenticate(user=self.user)
        try:
            self.assertEqual(
                self.client.post('/api/v1/wishlist/', {'product': self.product.id}, format='json').status_code,
                status.HTTP_201_CREATED,
            )
            self.assertEqual(
                self.client.post('/api/v1/wishlist/', {'product': self.product.id}, format='json').status_code,
                status.HTTP_200_OK,
            )
            self.assertEqual(
                self.client.delete(f'/api/v1/wishlist/{self.product.id}/').status_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
            )
        finally:
            SimpleRateThrottle.THROTTLE_RATES = original_rates
            cache.clear()
